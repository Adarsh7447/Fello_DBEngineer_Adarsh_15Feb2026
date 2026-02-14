"""
SQL Deployment Orchestrator
Executes DDL, Functions, Triggers, and RLS policies in correct order
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from utils.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class SQLDeployer:
    """
    Orchestrates SQL deployment from Supabase_replicate folder
    Executes scripts in correct dependency order
    """
    
    # Deployment order matters for dependencies
    DEPLOYMENT_ORDER = [
        ('DDL', 'CREATE_company_info_raw.sql'),
        ('DDL', 'CREATE_unified_company_member.sql'),
        ('DDL', 'CREATE_new_agents.sql'),
        ('DDL', 'CREATE_unified_merge_logs.sql'),
        ('DDL', 'CREATE_new_unified_agents.sql'),
        ('FUNCTIONS', 'helper_functions.sql'),
        ('FUNCTIONS', 'run_unified_member_pipeline.SQL'),
        ('FUNCTIONS', 'run_unified_merge_batch.sql'),
        ('TRIGGERS', 'TRG_new_unified_agents.sql'),
    ]
    
    def __init__(self, db_manager: DatabaseManager, sql_base_path: Path):
        """
        Initialize SQL deployer
        
        Args:
            db_manager: Database manager instance
            sql_base_path: Base path to Supabase_replicate folder
        """
        self.db_manager = db_manager
        self.sql_base_path = sql_base_path
        self.deployment_log = []
        
        if not self.sql_base_path.exists():
            raise FileNotFoundError(f"SQL base path not found: {self.sql_base_path}")
        
        logger.info(f"SQL Deployer initialized with base path: {self.sql_base_path}")
    
    def _load_sql_file(self, folder: str, filename: str) -> str:
        """
        Load SQL file content
        
        Args:
            folder: Folder name (DDL, FUNCTIONS, TRIGGERS, RLS)
            filename: SQL file name
            
        Returns:
            SQL file content
        """
        sql_path = self.sql_base_path / folder / filename
        
        if not sql_path.exists():
            raise FileNotFoundError(f"SQL file not found: {sql_path}")
        
        with open(sql_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.debug(f"Loaded SQL file: {sql_path}")
        return content
    
    def _execute_sql_script(self, sql_content: str, script_name: str, autocommit: bool = True) -> Dict[str, Any]:
        """
        Execute SQL script with error handling and logging
        
        Args:
            sql_content: SQL script content
            script_name: Name of the script for logging
            autocommit: Whether to use autocommit mode
            
        Returns:
            Execution result dictionary
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            logger.info(f"Executing: {script_name}")
            
            self.db_manager.execute_script(sql_content, autocommit=autocommit)
            
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'script': script_name,
                'status': 'success',
                'duration_seconds': duration,
                'timestamp': start_time.isoformat()
            }
            
            logger.info(f"✓ {script_name} executed successfully ({duration:.2f}s)")
            self.deployment_log.append(result)
            
            return result
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'script': script_name,
                'status': 'failed',
                'error': str(e),
                'duration_seconds': duration,
                'timestamp': start_time.isoformat()
            }
            
            logger.error(f"✗ {script_name} failed: {e}")
            self.deployment_log.append(result)
            
            raise
    
    def deploy_ddl(self, force_recreate: bool = False) -> List[Dict[str, Any]]:
        """
        Deploy all DDL scripts
        
        Args:
            force_recreate: If True, drop tables before creating (USE WITH CAUTION)
            
        Returns:
            List of deployment results
        """
        logger.info("=" * 70)
        logger.info("DEPLOYING DDL SCRIPTS")
        logger.info("=" * 70)
        
        results = []
        
        for folder, filename in self.DEPLOYMENT_ORDER:
            if folder == 'DDL':
                try:
                    sql_content = self._load_sql_file(folder, filename)
                    
                    # Add drop statement if force recreate
                    if force_recreate:
                        table_name = self._extract_table_name(filename)
                        if table_name:
                            drop_sql = f"DROP TABLE IF EXISTS {table_name} CASCADE;\n"
                            sql_content = drop_sql + sql_content
                            logger.warning(f"Force recreate enabled for {table_name}")
                    
                    result = self._execute_sql_script(sql_content, f"DDL/{filename}")
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"DDL deployment failed at {filename}: {e}")
                    raise
        
        logger.info(f"DDL deployment completed: {len(results)} scripts executed")
        return results
    
    def deploy_functions(self) -> List[Dict[str, Any]]:
        """
        Deploy all function scripts
        
        Returns:
            List of deployment results
        """
        logger.info("=" * 70)
        logger.info("DEPLOYING FUNCTIONS")
        logger.info("=" * 70)
        
        results = []
        
        for folder, filename in self.DEPLOYMENT_ORDER:
            if folder == 'FUNCTIONS':
                try:
                    sql_content = self._load_sql_file(folder, filename)
                    result = self._execute_sql_script(sql_content, f"FUNCTIONS/{filename}")
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Function deployment failed at {filename}: {e}")
                    raise
        
        logger.info(f"Function deployment completed: {len(results)} scripts executed")
        return results
    
    def deploy_triggers(self) -> List[Dict[str, Any]]:
        """
        Deploy all trigger scripts
        
        Returns:
            List of deployment results
        """
        logger.info("=" * 70)
        logger.info("DEPLOYING TRIGGERS")
        logger.info("=" * 70)
        
        results = []
        
        for folder, filename in self.DEPLOYMENT_ORDER:
            if folder == 'TRIGGERS':
                try:
                    sql_content = self._load_sql_file(folder, filename)
                    result = self._execute_sql_script(sql_content, f"TRIGGERS/{filename}")
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Trigger deployment failed at {filename}: {e}")
                    raise
        
        logger.info(f"Trigger deployment completed: {len(results)} scripts executed")
        return results
    
    def deploy_rls(self, enable: bool = True) -> Dict[str, Any]:
        """
        Deploy RLS (Row Level Security) policies
        
        Args:
            enable: Whether to enable RLS
            
        Returns:
            Deployment result
        """
        if not enable:
            logger.info("RLS deployment skipped (disabled in config)")
            return {'status': 'skipped', 'reason': 'disabled'}
        
        logger.info("=" * 70)
        logger.info("DEPLOYING RLS POLICIES")
        logger.info("=" * 70)
        
        try:
            sql_content = self._load_sql_file('RLS', 'RLS_enable_rls.sql')
            result = self._execute_sql_script(sql_content, 'RLS/RLS_enable_rls.sql')
            logger.info("RLS deployment completed")
            return result
            
        except Exception as e:
            logger.error(f"RLS deployment failed: {e}")
            raise
    
    def deploy_all(self, force_recreate: bool = False, enable_rls: bool = True) -> Dict[str, Any]:
        """
        Deploy all SQL components in correct order
        
        Args:
            force_recreate: If True, drop tables before creating
            enable_rls: Whether to enable RLS
            
        Returns:
            Complete deployment summary
        """
        logger.info("=" * 70)
        logger.info("STARTING FULL SQL DEPLOYMENT")
        logger.info("=" * 70)
        
        start_time = datetime.now(timezone.utc)
        
        try:
            # Step 1: Deploy DDL
            ddl_results = self.deploy_ddl(force_recreate=force_recreate)
            
            # Step 2: Deploy Functions
            function_results = self.deploy_functions()
            
            # Step 3: Deploy Triggers
            trigger_results = self.deploy_triggers()
            
            # Step 4: Deploy RLS
            rls_result = self.deploy_rls(enable=enable_rls)
            
            end_time = datetime.now(timezone.utc)
            total_duration = (end_time - start_time).total_seconds()
            
            summary = {
                'status': 'success',
                'total_duration_seconds': total_duration,
                'ddl_count': len(ddl_results),
                'function_count': len(function_results),
                'trigger_count': len(trigger_results),
                'rls_enabled': enable_rls,
                'deployment_log': self.deployment_log,
                'timestamp': start_time.isoformat()
            }
            
            logger.info("=" * 70)
            logger.info("DEPLOYMENT SUMMARY")
            logger.info("=" * 70)
            logger.info(f"Status: SUCCESS")
            logger.info(f"Total Duration: {total_duration:.2f}s")
            logger.info(f"DDL Scripts: {len(ddl_results)}")
            logger.info(f"Functions: {len(function_results)}")
            logger.info(f"Triggers: {len(trigger_results)}")
            logger.info(f"RLS Enabled: {enable_rls}")
            logger.info("=" * 70)
            
            return summary
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            total_duration = (end_time - start_time).total_seconds()
            
            logger.error("=" * 70)
            logger.error("DEPLOYMENT FAILED")
            logger.error("=" * 70)
            logger.error(f"Error: {e}")
            logger.error(f"Duration before failure: {total_duration:.2f}s")
            logger.error("=" * 70)
            
            return {
                'status': 'failed',
                'error': str(e),
                'total_duration_seconds': total_duration,
                'deployment_log': self.deployment_log,
                'timestamp': start_time.isoformat()
            }
    
    def verify_deployment(self) -> Dict[str, Any]:
        """
        Verify that all tables and functions were created successfully
        
        Returns:
            Verification results
        """
        logger.info("=" * 70)
        logger.info("VERIFYING DEPLOYMENT")
        logger.info("=" * 70)
        
        expected_tables = [
            ('bronze', 'company_info_raw'),
            ('public', 'unified_company_member'),
            ('public', 'new_agents'),
            ('public', 'unified_merge_logs'),
            ('public', 'new_unified_agents'),
        ]
        
        expected_functions = [
            'array_merge_unique',
            'update_last_updated_column',
            'run_unified_member_pipeline',
            'run_unified_merge_batch',
        ]
        
        verification = {
            'tables': {},
            'functions': {},
            'all_verified': True
        }
        
        # Check tables
        for schema, table in expected_tables:
            exists = self.db_manager.table_exists(table, schema)
            row_count = self.db_manager.get_row_count(table, schema) if exists else 0
            
            verification['tables'][f"{schema}.{table}"] = {
                'exists': exists,
                'row_count': row_count
            }
            
            if exists:
                logger.info(f"✓ Table {schema}.{table} exists ({row_count} rows)")
            else:
                logger.error(f"✗ Table {schema}.{table} NOT FOUND")
                verification['all_verified'] = False
        
        # Check functions
        for func_name in expected_functions:
            try:
                with self.db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM pg_proc p
                            JOIN pg_namespace n ON p.pronamespace = n.oid
                            WHERE n.nspname = 'public' AND p.proname = %s
                        )
                    """, (func_name,))
                    exists = cursor.fetchone()[0]
                    
                    verification['functions'][func_name] = exists
                    
                    if exists:
                        logger.info(f"✓ Function {func_name}() exists")
                    else:
                        logger.error(f"✗ Function {func_name}() NOT FOUND")
                        verification['all_verified'] = False
                        
            except Exception as e:
                logger.error(f"Error checking function {func_name}: {e}")
                verification['functions'][func_name] = False
                verification['all_verified'] = False
        
        logger.info("=" * 70)
        if verification['all_verified']:
            logger.info("✓ ALL COMPONENTS VERIFIED SUCCESSFULLY")
        else:
            logger.error("✗ VERIFICATION FAILED - Some components missing")
        logger.info("=" * 70)
        
        return verification
    
    def _extract_table_name(self, filename: str) -> Optional[str]:
        """
        Extract table name from DDL filename
        
        Args:
            filename: DDL filename (e.g., CREATE_new_agents.sql)
            
        Returns:
            Table name with schema or None
        """
        # Remove CREATE_ prefix and .sql suffix
        if filename.startswith('CREATE_') and filename.endswith('.sql'):
            table_name = filename[7:-4]  # Remove 'CREATE_' and '.sql'
            
            # Map to schema.table format
            schema_mapping = {
                'company_info_raw': 'bronze.company_info_raw',
                'unified_company_member': 'public.unified_company_member',
                'new_agents': 'public.new_agents',
                'unified_merge_logs': 'public.unified_merge_logs',
                'new_unified_agents': 'public.new_unified_agents',
            }
            
            return schema_mapping.get(table_name)
        
        return None
    
    def get_deployment_log(self) -> List[Dict[str, Any]]:
        """
        Get complete deployment log
        
        Returns:
            List of deployment events
        """
        return self.deployment_log
