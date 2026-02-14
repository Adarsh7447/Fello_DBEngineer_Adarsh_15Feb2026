#!/usr/bin/env python3
"""
Production-Grade Database Deployment Script
Orchestrates complete database setup: DDL, Functions, Triggers, RLS, and Data Loading
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any
import logging
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from utils.db_manager import DatabaseManager
from utils.config import ConfigManager
from deployer.sql_deployer import SQLDeployer
from deployer.data_loader import DataLoader


def setup_logging(log_level: str = 'INFO', log_file: str = None) -> None:
    """
    Configure logging with console and optional file output
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
    """
    log_format = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=handlers
    )
    
    # Reduce noise from psycopg2
    logging.getLogger('psycopg2').setLevel(logging.WARNING)


def save_deployment_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save deployment report to JSON file
    
    Args:
        report: Deployment report dictionary
        output_path: Path to save report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    logging.info(f"Deployment report saved to: {output_path}")


def deploy_database(
    force_recreate: bool = False,
    enable_rls: bool = True,
    load_data: bool = True,
    run_pipeline: bool = True,
    verify: bool = True
) -> Dict[str, Any]:
    """
    Execute complete database deployment
    
    Args:
        force_recreate: Drop and recreate tables (USE WITH CAUTION)
        enable_rls: Enable Row Level Security
        load_data: Load CSV data
        run_pipeline: Run data processing pipeline
        verify: Verify deployment
        
    Returns:
        Complete deployment report
    """
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("PRODUCTION DATABASE DEPLOYMENT")
    logger.info("=" * 80)
    
    start_time = datetime.now(timezone.utc)
    report = {
        'deployment_id': f"deploy_{start_time.strftime('%Y%m%d_%H%M%S')}",
        'start_time': start_time.isoformat(),
        'configuration': {
            'force_recreate': force_recreate,
            'enable_rls': enable_rls,
            'load_data': load_data,
            'run_pipeline': run_pipeline,
            'verify': verify
        }
    }
    
    try:
        # Initialize configuration
        logger.info("Initializing configuration...")
        config = ConfigManager()
        
        # Validate required environment variables
        required_vars = ['DATABASE_URL']
        if not config.validate_required_vars(required_vars):
            raise ValueError("Missing required environment variables")
        
        # Initialize database manager
        logger.info("Initializing database connection...")
        db_manager = DatabaseManager(config.database_url)
        
        # Test connection
        if not db_manager.test_connection():
            raise ConnectionError("Database connection test failed")
        
        # Get database info
        db_info = db_manager.get_database_info()
        report['database_info'] = db_info
        logger.info(f"Connected to: {db_info.get('database_name', 'unknown')}")
        
        # Determine paths
        base_path = Path(__file__).parent.parent
        sql_base_path = base_path / 'Supabase_replicate'
        csv_base_path = base_path / 'Supabase_replicate' / 'CSVs'
        
        logger.info(f"SQL Base Path: {sql_base_path}")
        logger.info(f"CSV Base Path: {csv_base_path}")
        
        # Initialize deployers
        sql_deployer = SQLDeployer(db_manager, sql_base_path)
        data_loader = DataLoader(db_manager, csv_base_path)
        
        # Step 1: Deploy SQL (DDL, Functions, Triggers, RLS)
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: SQL DEPLOYMENT")
        logger.info("=" * 80)
        
        sql_deployment = sql_deployer.deploy_all(
            force_recreate=force_recreate,
            enable_rls=enable_rls
        )
        report['sql_deployment'] = sql_deployment
        
        if sql_deployment['status'] != 'success':
            raise Exception("SQL deployment failed")
        
        # Step 2: Verify Deployment
        if verify:
            logger.info("\n" + "=" * 80)
            logger.info("STEP 2: VERIFICATION")
            logger.info("=" * 80)
            
            verification = sql_deployer.verify_deployment()
            report['verification'] = verification
            
            if not verification['all_verified']:
                logger.warning("Some components failed verification")
        
        # Step 3: Load Data
        if load_data:
            logger.info("\n" + "=" * 80)
            logger.info("STEP 3: DATA LOADING")
            logger.info("=" * 80)
            
            if run_pipeline:
                # Load data and run pipeline
                pipeline_result = data_loader.run_data_pipeline()
                report['data_pipeline'] = pipeline_result
                
                if pipeline_result['status'] != 'success':
                    raise Exception("Data pipeline failed")
            else:
                # Just load CSVs
                load_result = data_loader.load_all_csvs()
                report['data_load'] = load_result
                
                if load_result['status'] != 'success':
                    raise Exception("Data loading failed")
        
        # Calculate total duration
        end_time = datetime.now(timezone.utc)
        total_duration = (end_time - start_time).total_seconds()
        
        report['end_time'] = end_time.isoformat()
        report['total_duration_seconds'] = total_duration
        report['status'] = 'success'
        
        # Print final summary
        logger.info("\n" + "=" * 80)
        logger.info("DEPLOYMENT COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"Deployment ID: {report['deployment_id']}")
        logger.info(f"Total Duration: {total_duration:.2f}s")
        logger.info(f"Database: {db_info.get('database_name', 'unknown')}")
        
        if 'sql_deployment' in report:
            logger.info(f"DDL Scripts: {report['sql_deployment'].get('ddl_count', 0)}")
            logger.info(f"Functions: {report['sql_deployment'].get('function_count', 0)}")
            logger.info(f"Triggers: {report['sql_deployment'].get('trigger_count', 0)}")
        
        if 'data_pipeline' in report:
            stats = report['data_pipeline'].get('statistics', {})
            logger.info(f"Unified Agents: {stats.get('unified_agents_count', 0):,}")
        
        logger.info("=" * 80)
        
        return report
        
    except Exception as e:
        end_time = datetime.now(timezone.utc)
        total_duration = (end_time - start_time).total_seconds()
        
        report['end_time'] = end_time.isoformat()
        report['total_duration_seconds'] = total_duration
        report['status'] = 'failed'
        report['error'] = str(e)
        
        logger.error("\n" + "=" * 80)
        logger.error("DEPLOYMENT FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {e}")
        logger.error(f"Duration before failure: {total_duration:.2f}s")
        logger.error("=" * 80)
        
        return report
    
    finally:
        # Close database connections
        if 'db_manager' in locals():
            db_manager.close()


def main():
    """
    Main entry point for deployment script
    """
    parser = argparse.ArgumentParser(
        description='Production-Grade Database Deployment Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full deployment (DDL + Data + Pipeline)
  python deploy.py --full
  
  # DDL only (no data loading)
  python deploy.py --ddl-only
  
  # Force recreate tables (CAUTION: deletes existing data)
  python deploy.py --full --force-recreate
  
  # Skip RLS policies
  python deploy.py --full --no-rls
  
  # Load data only (assumes DDL already deployed)
  python deploy.py --data-only
        """
    )
    
    # Deployment modes
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--full', action='store_true',
                           help='Full deployment: DDL + Data + Pipeline')
    mode_group.add_argument('--ddl-only', action='store_true',
                           help='Deploy DDL, Functions, Triggers only (no data)')
    mode_group.add_argument('--data-only', action='store_true',
                           help='Load data and run pipeline only (assumes DDL exists)')
    
    # Options
    parser.add_argument('--force-recreate', action='store_true',
                       help='Drop and recreate tables (USE WITH CAUTION)')
    parser.add_argument('--no-rls', action='store_true',
                       help='Skip RLS (Row Level Security) deployment')
    parser.add_argument('--no-verify', action='store_true',
                       help='Skip deployment verification')
    parser.add_argument('--no-pipeline', action='store_true',
                       help='Load CSVs only, skip pipeline execution')
    
    # Logging
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level (default: INFO)')
    parser.add_argument('--log-file', type=str,
                       help='Log file path (optional)')
    
    # Output
    parser.add_argument('--report-file', type=str,
                       default='logs/deployment_report.json',
                       help='Deployment report output file')
    
    # Environment
    parser.add_argument('--env-file', type=str,
                       help='Path to .env file (optional)')
    
    args = parser.parse_args()
    
    # Load environment file if specified
    if args.env_file:
        env_path = Path(args.env_file)
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
            print(f"Loaded environment from: {env_path}")
        else:
            print(f"Warning: Environment file not found: {env_path}")
    else:
        # Try to load from default location
        default_env = Path(__file__).parent / '.env'
        if default_env.exists():
            load_dotenv(dotenv_path=default_env)
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    # Determine deployment parameters
    if args.full or (not args.ddl_only and not args.data_only):
        # Full deployment
        force_recreate = args.force_recreate
        enable_rls = not args.no_rls
        load_data = True
        run_pipeline = not args.no_pipeline
        verify = not args.no_verify
    elif args.ddl_only:
        # DDL only
        force_recreate = args.force_recreate
        enable_rls = not args.no_rls
        load_data = False
        run_pipeline = False
        verify = not args.no_verify
    elif args.data_only:
        # Data only
        force_recreate = False
        enable_rls = False
        load_data = True
        run_pipeline = not args.no_pipeline
        verify = False
    
    # Execute deployment
    report = deploy_database(
        force_recreate=force_recreate,
        enable_rls=enable_rls,
        load_data=load_data,
        run_pipeline=run_pipeline,
        verify=verify
    )
    
    # Save report
    report_path = Path(args.report_file)
    save_deployment_report(report, report_path)
    
    # Exit with appropriate code
    if report['status'] == 'success':
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
