#!/usr/bin/env python3
"""
Run Data Processing Pipeline
Execute unified member pipeline and merge batch
"""

import sys
from pathlib import Path
from datetime import datetime
import logging
import argparse

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


def run_member_pipeline(db_manager: DatabaseManager) -> dict:
    """Run unified member pipeline"""
    logger.info("=" * 70)
    logger.info("Running unified_member_pipeline...")
    logger.info("=" * 70)
    
    start_time = datetime.now()
    
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT public.run_unified_member_pipeline()")
        
        # Get count of processed records
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM public.unified_company_member 
                WHERE processed = false
            """)
            unprocessed = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM public.unified_company_member")
            total = cursor.fetchone()[0]
        
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✓ Pipeline completed in {duration:.2f}s")
        logger.info(f"Total records: {total:,}")
        logger.info(f"Unprocessed: {unprocessed:,}")
        
        return {
            'status': 'success',
            'duration_seconds': duration,
            'total_records': total,
            'unprocessed': unprocessed
        }
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return {
            'status': 'failed',
            'error': str(e)
        }


def run_merge_batch(db_manager: DatabaseManager) -> dict:
    """Run unified merge batch"""
    logger.info("=" * 70)
    logger.info("Running unified_merge_batch...")
    logger.info("=" * 70)
    
    start_time = datetime.now()
    
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT public.run_unified_merge_batch()")
        
        # Get statistics
        with db_manager.get_cursor(dict_cursor=True) as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_agents,
                    SUM(CASE WHEN needs_review THEN 1 ELSE 0 END) as needs_review,
                    ROUND(AVG(confidence_score), 2) as avg_confidence
                FROM public.new_unified_agents
            """)
            stats = cursor.fetchone()
            
            # Get last log entry
            cursor.execute("""
                SELECT total_processed, status
                FROM public.unified_merge_logs
                ORDER BY started_at DESC
                LIMIT 1
            """)
            log = cursor.fetchone()
        
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✓ Merge completed in {duration:.2f}s")
        logger.info(f"Total unified agents: {stats['total_agents']:,}")
        logger.info(f"Needs review: {stats['needs_review']:,}")
        logger.info(f"Avg confidence: {stats['avg_confidence']}")
        if log:
            logger.info(f"Records processed in this batch: {log['total_processed']:,}")
        
        return {
            'status': 'success',
            'duration_seconds': duration,
            'statistics': dict(stats),
            'batch_processed': log['total_processed'] if log else 0
        }
        
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        return {
            'status': 'failed',
            'error': str(e)
        }


def main():
    """Main pipeline execution"""
    parser = argparse.ArgumentParser(description='Run data processing pipeline')
    parser.add_argument('--member-only', action='store_true',
                       help='Run member pipeline only')
    parser.add_argument('--merge-only', action='store_true',
                       help='Run merge batch only')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    args = parser.parse_args()
    
    # Update log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    logger.info("=" * 70)
    logger.info("DATA PROCESSING PIPELINE")
    logger.info("=" * 70)
    
    try:
        # Initialize
        config = ConfigManager()
        db_manager = DatabaseManager(config.database_url)
        
        # Test connection
        if not db_manager.test_connection():
            logger.error("Database connection failed")
            sys.exit(1)
        
        overall_start = datetime.now()
        
        # Run pipelines
        if args.merge_only:
            merge_result = run_merge_batch(db_manager)
            success = merge_result['status'] == 'success'
        elif args.member_only:
            member_result = run_member_pipeline(db_manager)
            success = member_result['status'] == 'success'
        else:
            # Run both
            member_result = run_member_pipeline(db_manager)
            if member_result['status'] == 'success':
                merge_result = run_merge_batch(db_manager)
                success = merge_result['status'] == 'success'
            else:
                success = False
        
        overall_duration = (datetime.now() - overall_start).total_seconds()
        
        logger.info("=" * 70)
        if success:
            logger.info(f"✓ PIPELINE COMPLETED SUCCESSFULLY ({overall_duration:.2f}s)")
            sys.exit(0)
        else:
            logger.error(f"✗ PIPELINE FAILED ({overall_duration:.2f}s)")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)
    
    finally:
        if 'db_manager' in locals():
            db_manager.close()


if __name__ == '__main__':
    main()
