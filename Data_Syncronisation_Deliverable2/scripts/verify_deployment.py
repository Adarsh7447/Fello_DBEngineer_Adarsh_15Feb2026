#!/usr/bin/env python3
"""
Deployment Verification Script
Verifies database setup and data integrity
"""

import sys
from pathlib import Path
from datetime import datetime
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.db_manager import DatabaseManager
from utils.config import ConfigManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def verify_tables(db_manager: DatabaseManager) -> dict:
    """Verify all required tables exist"""
    logger.info("Verifying tables...")
    
    tables = [
        ('public', 'company_info_raw'),
        ('public', 'unified_company_member'),
        ('public', 'new_agents'),
        ('public', 'unified_merge_logs'),
        ('public', 'new_unified_agents'),
    ]
    
    results = {}
    all_ok = True
    
    for schema, table in tables:
        exists = db_manager.table_exists(table, schema)
        row_count = db_manager.get_row_count(table, schema) if exists else 0
        
        results[f"{schema}.{table}"] = {
            'exists': exists,
            'row_count': row_count
        }
        
        if exists:
            logger.info(f"✓ {schema}.{table}: {row_count:,} rows")
        else:
            logger.error(f"✗ {schema}.{table}: NOT FOUND")
            all_ok = False
    
    return {'all_ok': all_ok, 'tables': results}


def verify_functions(db_manager: DatabaseManager) -> dict:
    """Verify all required functions exist"""
    logger.info("Verifying functions...")
    
    functions = [
        'array_merge_unique',
        'update_last_updated_column',
        'run_unified_member_pipeline',
        'run_unified_merge_batch',
    ]
    
    results = {}
    all_ok = True
    
    for func_name in functions:
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM pg_proc p
                        JOIN pg_namespace n ON p.pronamespace = n.oid
                        WHERE n.nspname = 'public' AND p.proname = %s
                    )
                """, (func_name,))
                exists = cursor.fetchone()[0]
                
                results[func_name] = exists
                
                if exists:
                    logger.info(f"✓ {func_name}()")
                else:
                    logger.error(f"✗ {func_name}(): NOT FOUND")
                    all_ok = False
                    
        except Exception as e:
            logger.error(f"✗ {func_name}(): Error - {e}")
            results[func_name] = False
            all_ok = False
    
    return {'all_ok': all_ok, 'functions': results}


def verify_data_quality(db_manager: DatabaseManager) -> dict:
    """Verify data quality in unified_agents table"""
    logger.info("Verifying data quality...")
    
    try:
        with db_manager.get_cursor(dict_cursor=True) as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    SUM(CASE WHEN needs_review THEN 1 ELSE 0 END) as needs_review,
                    ROUND(AVG(confidence_score), 2) as avg_confidence,
                    MIN(confidence_score) as min_confidence,
                    MAX(confidence_score) as max_confidence,
                    COUNT(DISTINCT source_team_id) as unique_teams
                FROM public.new_unified_agents
            """)
            stats = cursor.fetchone()
            
            logger.info(f"Total Records: {stats['total_records']:,}")
            logger.info(f"Needs Review: {stats['needs_review']:,}")
            logger.info(f"Avg Confidence: {stats['avg_confidence']}")
            logger.info(f"Confidence Range: {stats['min_confidence']} - {stats['max_confidence']}")
            logger.info(f"Unique Teams: {stats['unique_teams']:,}")
            
            return {
                'all_ok': True,
                'statistics': dict(stats)
            }
            
    except Exception as e:
        logger.error(f"Data quality check failed: {e}")
        return {'all_ok': False, 'error': str(e)}


def verify_indexes(db_manager: DatabaseManager) -> dict:
    """Verify critical indexes exist"""
    logger.info("Verifying indexes...")
    
    try:
        with db_manager.get_cursor(dict_cursor=True) as cursor:
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname
                FROM pg_indexes
                WHERE schemaname IN ('public', 'bronze')
                AND tablename IN ('new_unified_agents', 'unified_company_member', 'new_agents')
                ORDER BY tablename, indexname
            """)
            indexes = cursor.fetchall()
            
            index_count = len(indexes)
            logger.info(f"Found {index_count} indexes")
            
            for idx in indexes:
                logger.info(f"  - {idx['tablename']}.{idx['indexname']}")
            
            return {
                'all_ok': index_count > 0,
                'index_count': index_count,
                'indexes': [dict(idx) for idx in indexes]
            }
            
    except Exception as e:
        logger.error(f"Index verification failed: {e}")
        return {'all_ok': False, 'error': str(e)}


def main():
    """Main verification routine"""
    logger.info("=" * 70)
    logger.info("DATABASE DEPLOYMENT VERIFICATION")
    logger.info("=" * 70)
    
    try:
        # Initialize
        config = ConfigManager()
        db_manager = DatabaseManager(config.database_url)
        
        # Test connection
        if not db_manager.test_connection():
            logger.error("Database connection failed")
            sys.exit(1)
        
        # Get database info
        db_info = db_manager.get_database_info()
        logger.info(f"Database: {db_info.get('database_name')}")
        logger.info(f"Version: {db_info.get('version', 'unknown')[:50]}...")
        logger.info("")
        
        # Run verifications
        table_results = verify_tables(db_manager)
        logger.info("")
        
        function_results = verify_functions(db_manager)
        logger.info("")
        
        index_results = verify_indexes(db_manager)
        logger.info("")
        
        data_results = verify_data_quality(db_manager)
        logger.info("")
        
        # Summary
        logger.info("=" * 70)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 70)
        
        all_passed = (
            table_results['all_ok'] and
            function_results['all_ok'] and
            index_results['all_ok'] and
            data_results['all_ok']
        )
        
        if all_passed:
            logger.info("✓ ALL CHECKS PASSED")
            logger.info("Database is properly configured and ready for use")
            sys.exit(0)
        else:
            logger.error("✗ SOME CHECKS FAILED")
            logger.error("Review errors above and re-run deployment if needed")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)
    
    finally:
        if 'db_manager' in locals():
            db_manager.close()


if __name__ == '__main__':
    main()
