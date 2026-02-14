"""
Database Connection Manager
Handles PostgreSQL/Supabase connections with connection pooling and error handling
"""

import os
from contextlib import contextmanager
from typing import Optional, Dict, Any
import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Production-ready database connection manager with pooling
    """
    
    def __init__(self, connection_string: Optional[str] = None, min_conn: int = 1, max_conn: int = 10):
        """
        Initialize database manager with connection pooling
        
        Args:
            connection_string: PostgreSQL connection string (defaults to env var)
            min_conn: Minimum connections in pool
            max_conn: Maximum connections in pool
        """
        self.connection_string = connection_string or os.getenv('DATABASE_URL')
        
        if not self.connection_string:
            raise ValueError("Database connection string not provided. Set DATABASE_URL environment variable.")
        
        try:
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                min_conn,
                max_conn,
                self.connection_string
            )
            logger.info(f"Database connection pool created (min={min_conn}, max={max_conn})")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self, dict_cursor: bool = False):
        """
        Context manager for database connections
        
        Args:
            dict_cursor: If True, returns results as dictionaries
            
        Yields:
            Database connection
        """
        conn = None
        try:
            conn = self.connection_pool.getconn()
            if dict_cursor:
                conn.cursor_factory = RealDictCursor
            logger.debug("Connection acquired from pool")
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                self.connection_pool.putconn(conn)
                logger.debug("Connection returned to pool")
    
    @contextmanager
    def get_cursor(self, dict_cursor: bool = False, autocommit: bool = False):
        """
        Context manager for database cursor
        
        Args:
            dict_cursor: If True, returns results as dictionaries
            autocommit: If True, enables autocommit mode
            
        Yields:
            Database cursor
        """
        with self.get_connection(dict_cursor=dict_cursor) as conn:
            if autocommit:
                conn.autocommit = True
            cursor = conn.cursor()
            try:
                yield cursor
                if not autocommit:
                    conn.commit()
            except Exception as e:
                if not autocommit:
                    conn.rollback()
                raise
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: Optional[tuple] = None, fetch: bool = True) -> Optional[list]:
        """
        Execute a query and optionally fetch results
        
        Args:
            query: SQL query to execute
            params: Query parameters
            fetch: Whether to fetch results
            
        Returns:
            Query results if fetch=True, None otherwise
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            return None
    
    def execute_script(self, script: str, autocommit: bool = True) -> None:
        """
        Execute a SQL script (potentially multiple statements)
        
        Args:
            script: SQL script content
            autocommit: Whether to use autocommit mode
        """
        with self.get_cursor(autocommit=autocommit) as cursor:
            cursor.execute(script)
            logger.debug("SQL script executed successfully")
    
    def test_connection(self) -> bool:
        """
        Test database connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                logger.info("Database connection test successful")
                return result[0] == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get database information
        
        Returns:
            Dictionary with database metadata
        """
        try:
            with self.get_cursor(dict_cursor=True) as cursor:
                cursor.execute("""
                    SELECT 
                        current_database() as database_name,
                        current_user as user_name,
                        version() as version,
                        pg_size_pretty(pg_database_size(current_database())) as database_size
                """)
                result = cursor.fetchone()
                logger.info(f"Connected to database: {result['database_name']}")
                return dict(result)
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {}
    
    def table_exists(self, table_name: str, schema: str = 'public') -> bool:
        """
        Check if a table exists
        
        Args:
            table_name: Name of the table
            schema: Schema name (default: public)
            
        Returns:
            True if table exists, False otherwise
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = %s 
                        AND table_name = %s
                    )
                """, (schema, table_name))
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error checking table existence: {e}")
            return False
    
    def get_row_count(self, table_name: str, schema: str = 'public') -> int:
        """
        Get row count for a table
        
        Args:
            table_name: Name of the table
            schema: Schema name (default: public)
            
        Returns:
            Number of rows in the table
        """
        try:
            with self.get_cursor() as cursor:
                query = sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                    sql.Identifier(schema),
                    sql.Identifier(table_name)
                )
                cursor.execute(query)
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting row count for {schema}.{table_name}: {e}")
            return -1
    
    def close(self):
        """
        Close all connections in the pool
        """
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("All database connections closed")
