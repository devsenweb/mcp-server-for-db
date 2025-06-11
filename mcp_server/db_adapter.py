"""
Database Adapter for MCP Server

Author: devsen
"""

from sqlalchemy import create_engine, MetaData, text, inspect
from sqlalchemy.exc import SQLAlchemyError
import yaml
import os
import logging
import re
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseAdapter:
    def __init__(self, db_uri: Optional[str] = None):
        """
        Initialize the database adapter for MCP operations.
        
        Args:
            db_uri: Database connection URI. If None, loads from config.yaml
        """
        self.db_uri = self._get_database_uri(db_uri)
        
        # Create engine with basic connection pooling
        self.engine = create_engine(
            self.db_uri,
            pool_pre_ping=True,  # Validate connections before use
            echo=False  # Set to True for SQL debugging
        )
        
        self.metadata = MetaData()
        self.inspector = inspect(self.engine)
        
        # Load database schema
        self._refresh_metadata()
        
        logger.info(f"Database adapter initialized with {len(self.metadata.tables)} tables")

    def _get_database_uri(self, db_uri: Optional[str]) -> str:
        """Get database URI from parameter or config file."""
        if db_uri:
            return db_uri
            
        # Load from config.yaml
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
            
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config['db']['uri']
        except (KeyError, yaml.YAMLError) as e:
            raise ValueError(f"Error reading database URI from config: {e}")

    def _refresh_metadata(self):
        """Load database schema information."""
        try:
            self.metadata.clear()
            self.metadata.reflect(bind=self.engine)
            logger.info("Database metadata loaded")
        except SQLAlchemyError as e:
            logger.error(f"Error loading metadata: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        connection = None
        try:
            connection = self.engine.connect()
            yield connection
        except SQLAlchemyError as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection:
                connection.close()

    def get_schema(self) -> Dict[str, Any]:
        """
        Get database schema information for LLM context.
        
        Returns:
            Simple schema dictionary with table and column information
        """
        try:
            schema = {
                'tables': {},
                'database_type': self.engine.dialect.name
            }
            
            for table in self.metadata.sorted_tables:
                columns = []
                for column in table.columns:
                    col_info = {
                        'name': column.name,
                        'type': str(column.type),
                        'nullable': column.nullable,
                        'primary_key': column.primary_key
                    }
                    columns.append(col_info)
                
                schema['tables'][table.name] = {
                    'columns': columns
                }
            
            return schema
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting schema: {e}")
            return {'tables': {}, 'error': str(e)}

    def get_tables(self) -> List[str]:
        """
        Get list of all table names.
        
        Returns:
            List of table names
        """
        try:
            return [table.name for table in self.metadata.sorted_tables]
        except Exception as e:
            logger.error(f"Error getting tables: {e}")
            return []

    def validate_sql(self, query: str) -> bool:
        """
        Basic SQL validation for safety.
        
        Args:
            query: SQL query to validate
            
        Returns:
            True if query appears safe, False otherwise
        """
        try:
            # Basic safety check - only allow SELECT queries
            query_clean = query.strip().upper()
            
            if not query_clean.startswith('SELECT'):
                logger.warning("Only SELECT queries are allowed")
                return False
            
            # Block dangerous keywords even in SELECT
            dangerous_keywords = [
                'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE',
                'TRUNCATE', 'EXEC', 'EXECUTE', 'CALL', 'LOAD_FILE', 'INTO OUTFILE'
            ]
            
            for keyword in dangerous_keywords:
                if keyword in query_clean:
                    logger.warning(f"Blocked dangerous keyword: {keyword}")
                    return False
            
            # Check for basic SQL injection patterns
            injection_patterns = [
                r';\s*\w+',  # Multiple statements
                r'--',       # SQL comments
                r'/\*.*\*/', # Block comments
                r'@@\w+',    # System variables
            ]
            
            for pattern in injection_patterns:
                if re.search(pattern, query_clean):
                    logger.warning(f"Blocked suspicious pattern: {pattern}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating SQL: {e}")
            return False

    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a SELECT query and return results.
        
        Args:
            query: SQL SELECT query to execute
            params: Optional query parameters
            
        Returns:
            Dictionary containing query results
        """
        try:
            # Validate query
            if not self.validate_sql(query):
                return {
                    'status': 'error',
                    'message': 'Query validation failed - only safe SELECT queries are allowed',
                    'data': []
                }
            
            # Add LIMIT if not present to prevent huge results
            if 'LIMIT' not in query.upper():
                query = f"{query.rstrip(';')} LIMIT 1000"
            
            with self.get_connection() as connection:
                if params:
                    result = connection.execute(text(query), params)
                else:
                    result = connection.execute(text(query))
                
                # Convert results to simple format
                columns = list(result.keys())
                rows = []
                
                for row in result.fetchall():
                    row_dict = {}
                    for i, value in enumerate(row):
                        column_name = columns[i]
                        # Handle special types for JSON serialization
                        if hasattr(value, 'isoformat'):  # datetime objects
                            row_dict[column_name] = value.isoformat()
                        elif isinstance(value, (bytes, bytearray)):
                            row_dict[column_name] = value.decode('utf-8', errors='replace')
                        else:
                            row_dict[column_name] = value
                    rows.append(row_dict)
                
                return {
                    'status': 'success',
                    'data': rows,
                    'row_count': len(rows),
                    'columns': columns
                }
                    
        except SQLAlchemyError as e:
            logger.error(f"SQL execution error: {e}")
            return {
                'status': 'error',
                'message': f"Database error: {str(e)}",
                'data': []
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                'status': 'error',
                'message': f"Unexpected error: {str(e)}",
                'data': []
            }

    def test_connection(self) -> Dict[str, Any]:
        """
        Test database connection.
        
        Returns:
            Connection test results
        """
        try:
            with self.get_connection() as conn:
                conn.execute(text("SELECT 1"))
            
            return {
                'status': 'success',
                'message': 'Database connection successful',
                'database_type': self.engine.dialect.name,
                'table_count': len(self.metadata.tables)
            }
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                'status': 'error',
                'message': f"Connection failed: {str(e)}"
            }

    def get_sample_data(self, table_name: str, limit: int = 5) -> Dict[str, Any]:
        """
        Get sample data from a table for context.
        
        Args:
            table_name: Name of the table
            limit: Number of sample rows to return
            
        Returns:
            Sample data from the table
        """
        try:
            if table_name not in [t.name for t in self.metadata.sorted_tables]:
                return {
                    'status': 'error',
                    'message': f'Table {table_name} not found'
                }
            
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            return self.execute_query(query)
            
        except Exception as e:
            logger.error(f"Error getting sample data: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'data': []
            }

    def close(self):
        """Close database connections."""
        try:
            self.engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")

    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            self.close()
        except:
            pass