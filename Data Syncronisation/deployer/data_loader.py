"""
Data Loader
Handles CSV data loading into database tables
"""

import sys
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from utils.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Handles loading CSV data into database tables
    """
    
    # CSV to table mapping
    CSV_TABLE_MAPPING = {
        'raw_company_info.csv': ('public', 'company_info_raw'),
        'new_agents.csv': ('public', 'new_agents'),
    }
    
    def __init__(self, db_manager: DatabaseManager, csv_base_path: Path):
        """
        Initialize data loader
        
        Args:
            db_manager: Database manager instance
            csv_base_path: Base path to CSV files folder
        """
        self.db_manager = db_manager
        self.csv_base_path = csv_base_path
        self.load_log = []
        
        if not self.csv_base_path.exists():
            raise FileNotFoundError(f"CSV base path not found: {self.csv_base_path}")
        
        logger.info(f"Data Loader initialized with CSV path: {self.csv_base_path}")
    
    def _get_csv_path(self, csv_filename: str) -> Path:
        """
        Get full path to CSV file
        
        Args:
            csv_filename: CSV file name
            
        Returns:
            Full path to CSV file
        """
        csv_path = self.csv_base_path / csv_filename
        
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        return csv_path
    
    def _load_csv_with_copy(self, csv_path: Path, schema: str, table: str) -> int:
        """
        Load CSV using PostgreSQL COPY command (fastest method)
        
        Args:
            csv_path: Path to CSV file
            schema: Database schema
            table: Table name
            
        Returns:
            Number of rows loaded
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                # Use COPY command for bulk loading
                with open(csv_path, 'r', encoding='utf-8') as f:
                    # Skip header row
                    next(f)
                    
                    copy_sql = f"""
                        COPY {schema}.{table}
                        FROM STDIN
                        WITH (FORMAT csv, HEADER false, DELIMITER ',', NULL '')
                    """
                    
                    cursor.copy_expert(copy_sql, f)
                    row_count = cursor.rowcount
                    
                logger.info(f"Loaded {row_count} rows into {schema}.{table}")
                return row_count
                
        except Exception as e:
            logger.error(f"Failed to load CSV using COPY: {e}")
            raise
    
    def _load_csv_with_insert(self, csv_path: Path, schema: str, table: str, batch_size: int = 1000) -> int:
        """
        Load CSV using INSERT statements (fallback method)
        
        Args:
            csv_path: Path to CSV file
            schema: Database schema
            table: Table name
            batch_size: Number of rows per batch
            
        Returns:
            Number of rows loaded
        """
        try:
            total_rows = 0
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                columns = reader.fieldnames
                
                if not columns:
                    raise ValueError(f"No columns found in CSV: {csv_path}")
                
                batch = []
                
                for row in reader:
                    batch.append(row)
                    
                    if len(batch) >= batch_size:
                        self._insert_batch(schema, table, columns, batch)
                        total_rows += len(batch)
                        batch = []
                
                # Insert remaining rows
                if batch:
                    self._insert_batch(schema, table, columns, batch)
                    total_rows += len(batch)
            
            logger.info(f"Loaded {total_rows} rows into {schema}.{table}")
            return total_rows
            
        except Exception as e:
            logger.error(f"Failed to load CSV using INSERT: {e}")
            raise
    
    def _insert_batch(self, schema: str, table: str, columns: List[str], rows: List[Dict[str, Any]]) -> None:
        """
        Insert a batch of rows
        
        Args:
            schema: Database schema
            table: Table name
            columns: Column names
            rows: List of row dictionaries
        """
        if not rows:
            return
        
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)
        
        insert_sql = f"""
            INSERT INTO {schema}.{table} ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
        """
        
        with self.db_manager.get_cursor() as cursor:
            for row in rows:
                values = [row.get(col) for col in columns]
                cursor.execute(insert_sql, values)
    
    def load_csv(self, csv_filename: str, use_copy: bool = True) -> Dict[str, Any]:
        """
        Load a single CSV file into its corresponding table
        
        Args:
            csv_filename: CSV file name
            use_copy: Whether to use COPY command (faster) or INSERT (more compatible)
            
        Returns:
            Load result dictionary
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Get table mapping
            if csv_filename not in self.CSV_TABLE_MAPPING:
                raise ValueError(f"No table mapping found for CSV: {csv_filename}")
            
            schema, table = self.CSV_TABLE_MAPPING[csv_filename]
            csv_path = self._get_csv_path(csv_filename)
            
            logger.info(f"Loading {csv_filename} into {schema}.{table}")
            
            # Check if table exists
            if not self.db_manager.table_exists(table, schema):
                raise ValueError(f"Table {schema}.{table} does not exist. Run DDL deployment first.")
            
            # Load data
            if use_copy:
                try:
                    row_count = self._load_csv_with_copy(csv_path, schema, table)
                except Exception as e:
                    logger.warning(f"COPY failed, falling back to INSERT: {e}")
                    row_count = self._load_csv_with_insert(csv_path, schema, table)
            else:
                row_count = self._load_csv_with_insert(csv_path, schema, table)
            
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'csv_file': csv_filename,
                'table': f"{schema}.{table}",
                'status': 'success',
                'rows_loaded': row_count,
                'duration_seconds': duration,
                'timestamp': start_time.isoformat()
            }
            
            logger.info(f"✓ {csv_filename} loaded successfully ({row_count} rows, {duration:.2f}s)")
            self.load_log.append(result)
            
            return result
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'csv_file': csv_filename,
                'status': 'failed',
                'error': str(e),
                'duration_seconds': duration,
                'timestamp': start_time.isoformat()
            }
            
            logger.error(f"✗ {csv_filename} load failed: {e}")
            self.load_log.append(result)
            
            raise
    
    def load_all_csvs(self, use_copy: bool = True) -> Dict[str, Any]:
        """
        Load all CSV files
        
        Args:
            use_copy: Whether to use COPY command
            
        Returns:
            Complete load summary
        """
        logger.info("=" * 70)
        logger.info("LOADING CSV DATA")
        logger.info("=" * 70)
        
        start_time = datetime.now(timezone.utc)
        results = []
        total_rows = 0
        
        try:
            for csv_filename in self.CSV_TABLE_MAPPING.keys():
                csv_path = self.csv_base_path / csv_filename
                
                if not csv_path.exists():
                    logger.warning(f"CSV file not found, skipping: {csv_filename}")
                    continue
                
                result = self.load_csv(csv_filename, use_copy=use_copy)
                results.append(result)
                total_rows += result.get('rows_loaded', 0)
            
            end_time = datetime.now(timezone.utc)
            total_duration = (end_time - start_time).total_seconds()
            
            summary = {
                'status': 'success',
                'total_duration_seconds': total_duration,
                'files_loaded': len(results),
                'total_rows': total_rows,
                'load_log': self.load_log,
                'timestamp': start_time.isoformat()
            }
            
            logger.info("=" * 70)
            logger.info("CSV LOAD SUMMARY")
            logger.info("=" * 70)
            logger.info(f"Status: SUCCESS")
            logger.info(f"Total Duration: {total_duration:.2f}s")
            logger.info(f"Files Loaded: {len(results)}")
            logger.info(f"Total Rows: {total_rows:,}")
            logger.info("=" * 70)
            
            return summary
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            total_duration = (end_time - start_time).total_seconds()
            
            logger.error("=" * 70)
            logger.error("CSV LOAD FAILED")
            logger.error("=" * 70)
            logger.error(f"Error: {e}")
            logger.error(f"Duration before failure: {total_duration:.2f}s")
            logger.error("=" * 70)
            
            return {
                'status': 'failed',
                'error': str(e),
                'total_duration_seconds': total_duration,
                'load_log': self.load_log,
                'timestamp': start_time.isoformat()
            }
    
    def run_data_pipeline(self) -> Dict[str, Any]:
        """
        Run the complete data processing pipeline
        1. Load CSVs
        2. Run unified_member_pipeline
        3. Run unified_merge_batch
        
        Returns:
            Pipeline execution summary
        """
        logger.info("=" * 70)
        logger.info("RUNNING DATA PROCESSING PIPELINE")
        logger.info("=" * 70)
        
        start_time = datetime.now(timezone.utc)
        
        try:
            # Step 1: Load CSVs
            load_summary = self.load_all_csvs()
            
            if load_summary['status'] != 'success':
                raise Exception("CSV loading failed")
            
            # Step 2: Run unified_member_pipeline
            logger.info("Running unified_member_pipeline...")
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT public.run_unified_member_pipeline()")
            logger.info("✓ unified_member_pipeline completed")
            
            # Step 3: Run unified_merge_batch
            logger.info("Running unified_merge_batch...")
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT public.run_unified_merge_batch()")
            logger.info("✓ unified_merge_batch completed")
            
            # Get final statistics
            stats = self._get_pipeline_stats()
            
            end_time = datetime.now(timezone.utc)
            total_duration = (end_time - start_time).total_seconds()
            
            summary = {
                'status': 'success',
                'total_duration_seconds': total_duration,
                'csv_load_summary': load_summary,
                'statistics': stats,
                'timestamp': start_time.isoformat()
            }
            
            logger.info("=" * 70)
            logger.info("PIPELINE EXECUTION SUMMARY")
            logger.info("=" * 70)
            logger.info(f"Status: SUCCESS")
            logger.info(f"Total Duration: {total_duration:.2f}s")
            logger.info(f"Unified Agents: {stats.get('unified_agents_count', 0):,}")
            logger.info(f"Needs Review: {stats.get('needs_review_count', 0):,}")
            logger.info("=" * 70)
            
            return summary
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            total_duration = (end_time - start_time).total_seconds()
            
            logger.error("=" * 70)
            logger.error("PIPELINE EXECUTION FAILED")
            logger.error("=" * 70)
            logger.error(f"Error: {e}")
            logger.error(f"Duration before failure: {total_duration:.2f}s")
            logger.error("=" * 70)
            
            return {
                'status': 'failed',
                'error': str(e),
                'total_duration_seconds': total_duration,
                'timestamp': start_time.isoformat()
            }
    
    def _get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Get pipeline statistics
        
        Returns:
            Statistics dictionary
        """
        try:
            with self.db_manager.get_cursor(dict_cursor=True) as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_count,
                        SUM(CASE WHEN needs_review THEN 1 ELSE 0 END) as needs_review_count,
                        ROUND(AVG(confidence_score), 2) as avg_confidence
                    FROM public.new_unified_agents
                """)
                result = cursor.fetchone()
                
                return {
                    'unified_agents_count': result['total_count'],
                    'needs_review_count': result['needs_review_count'],
                    'avg_confidence': float(result['avg_confidence']) if result['avg_confidence'] else 0
                }
        except Exception as e:
            logger.error(f"Failed to get pipeline stats: {e}")
            return {}
    
    def get_load_log(self) -> List[Dict[str, Any]]:
        """
        Get complete load log
        
        Returns:
            List of load events
        """
        return self.load_log
