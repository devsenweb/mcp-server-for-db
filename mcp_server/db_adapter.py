"""
Database Adapter for MCP Server

Author: devsen
"""

from sqlalchemy import create_engine, MetaData, text, inspect, Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import URL
import yaml
import os
import logging
from typing import Dict, List, Any, Optional, Union
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseAdapter:
    def __init__(self, config_path: Optional[Union[str, dict]] = None, db_uri: Optional[str] = None):
        """
        Initialize the database adapter for MCP operations.
        
        Args:
            config_path: Path to config file or dict with config. If None, loads from config.yaml
            db_uri: Optional database URI (overrides config if provided)
        """
        if db_uri:
            # Use provided URI directly
            self.db_uri = db_uri
            self.config = {
                'database': {
                    'uri': db_uri,
                    'pool_size': 5,
                    'max_overflow': 10,
                    'pool_timeout': 30,
                    'pool_recycle': 3600,
                    'pool_pre_ping': True,
                    'echo': False
                }
            }
        else:
            # Load config from file or dict
            if isinstance(config_path, dict):
                self.config = config_path
            else:
                self.config = self._load_config(config_path)
            
            self.db_uri = self.config['database']['uri']
        
        # Initialize SQLAlchemy engine with connection pooling
        self.engine = self._create_engine()
        self.metadata = MetaData()
        self.inspector = inspect(self.engine)
        
        # Load database schema
        self._refresh_metadata()
        
        logger.info(f"Database adapter initialized for {self.db_uri}")
        logger.info(f"Database type: {self.engine.dialect.name}")
        logger.info(f"Tables found: {len(self.metadata.tables)}")

    def _load_config(self, config_path: Optional[str] = None) -> dict:
        """Load configuration from YAML file or use defaults."""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config.yaml'
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
            
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Set default values if not specified
            db_config = config.setdefault('database', {})
            db_config.setdefault('pool_size', 5)
            db_config.setdefault('max_overflow', 10)
            db_config.setdefault('pool_timeout', 30)
            db_config.setdefault('pool_recycle', 3600)
            db_config.setdefault('pool_pre_ping', True)
            db_config.setdefault('echo', False)
            
            if 'uri' not in db_config:
                raise ValueError("Database URI not found in configuration")
                
            return config
            
        except (yaml.YAMLError, KeyError) as e:
            raise ValueError(f"Error reading configuration: {e}")
    
    def _create_engine(self) -> Engine:
        """Create and configure SQLAlchemy engine."""
        db_config = self.config['database']
        
        try:
            engine = create_engine(
                db_config['uri'],
                pool_size=db_config['pool_size'],
                max_overflow=db_config['max_overflow'],
                pool_timeout=db_config['pool_timeout'],
                pool_recycle=db_config['pool_recycle'],
                pool_pre_ping=db_config['pool_pre_ping'],
                echo=db_config['echo']
            )
            
            # Test the connection
            with engine.connect() as conn:
                conn.execute(text('SELECT 1'))
                
            return engine
            
        except Exception as e:
            raise ValueError(f"Failed to connect to database: {str(e)}")

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
        Get database schema information.
        
        Returns:
            Dictionary with table and column information
        """
        try:
            schema = {
                'tables': {},
                'database_type': self.engine.dialect.name
            }
            
            for table_name in self.inspector.get_table_names():
                schema['tables'][table_name] = {
                    'columns': [col['name'] for col in self.inspector.get_columns(table_name)],
                    'primary_key': self.inspector.get_pk_constraint(table_name).get('constrained_columns', [])
                }
                
            return schema
            
        except Exception as e:
            logger.error(f"Error getting schema: {e}")
            return {
                'tables': {},
                'database_type': self.engine.dialect.name,
                'error': str(e)
            }
            
    def get_tables(self) -> List[str]:
        """
        Get list of all tables in the database.
        
        Returns:
            List of table names
        """
        return self.inspector.get_table_names()
        
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """
        Execute a SQL query and return results.
        
        Args:
            sql: SQL query to execute
            
        Returns:
            Dictionary containing query results and metadata
        """
        try:
            with self.get_connection() as conn:
                result = conn.execute(text(sql))
                
                if result.returns_rows:
                    columns = list(result.keys())
                    rows = [dict(zip(columns, row)) for row in result.fetchall()]
                    return {
                        'rowcount': result.rowcount,
                        'columns': columns,
                        'data': rows
                    }
                else:
                    return {
                        'rowcount': result.rowcount,
                        'message': f'Query OK, {result.rowcount} rows affected'
                    }
                    
        except Exception as e:
            raise ValueError(f"Error executing query: {str(e)}")

    def execute_query_with_params(self, query: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a SQL query with parameters and return results.
        
        Args:
            query: SQL query to execute
            params: Dictionary of query parameters
            
        Returns:
            Dictionary containing query results and metadata
        """
        try:
            with self.get_connection() as conn:
                result = conn.execute(text(query), params)
                
                if result.returns_rows:
                    columns = list(result.keys())
                    rows = [dict(zip(columns, row)) for row in result.fetchall()]
                    return {
                        'rowcount': result.rowcount,
                        'columns': columns,
                        'data': rows
                    }
                else:
                    return {
                        'rowcount': result.rowcount,
                        'message': f'Query OK, {result.rowcount} rows affected'
                    }
                    
        except Exception as e:
            raise ValueError(f"Error executing query: {str(e)}")

    def execute_script(self, script: str) -> Dict[str, Any]:
        """
        Execute a SQL script and return results.
        
        Args:
            script: SQL script to execute
            
        Returns:
            Dictionary containing query results and metadata
        """
        try:
            with self.get_connection() as conn:
                statements = [s.strip() for s in script.split(';') if s.strip()]
                
                results = []
                
                for stmt in statements:
                    result = conn.execute(text(stmt))
                    
                    if result.returns_rows:
                        columns = list(result.keys())
                        rows = [dict(zip(columns, row)) for row in result.fetchall()]
                        results.append({
                            'statement': stmt,
                            'data': rows,
                            'rowcount': len(rows)
                        })
                    else:
                        results.append({
                            'statement': stmt,
                            'rowcount': result.rowcount
                        })
                
                return {
                    'status': 'success',
                    'message': f'Executed {len(results)} statements successfully',
                    'statements': results,
                    'rowcount': sum(r.get('rowcount', 0) for r in results)
                }
                    
        except Exception as e:
            raise ValueError(f"Error executing script: {str(e)}")

    def _validate_single_statement(self, query: str) -> bool:
        """Validate a single SQL statement."""
        query_clean = query.strip().upper()
        
        # Allow only DML operations (SELECT, INSERT, UPDATE, DELETE)
        if not any(query_clean.startswith(cmd) for cmd in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
            logger.warning(f"Only DML operations (SELECT, INSERT, UPDATE, DELETE) are allowed. Got: {query_clean.split()[0] if query_clean.split() else 'empty'}")
            return False
        
        # Block dangerous keywords
        dangerous_keywords = [
            'DROP', 'ALTER', 'CREATE', 'TRUNCATE', 'EXEC', 'EXECUTE', 
            'CALL', 'LOAD_FILE', 'INTO OUTFILE', 'GRANT', 'REVOKE',
            'SHUTDOWN', 'KILL', 'LOCK', 'UNLOCK', 'ANALYZE', 'ATTACH',
            'DETACH', 'VACUUM', 'REINDEX', 'REPLACE', 'MERGE', 'EXPLAIN',
            'PRAGMA', 'SAVEPOINT', 'RELEASE', 'CURSOR', 'TRANSACTION',
            ';'  # Prevent multiple statements
        ]
        
        # Check for dangerous keywords
        for keyword in dangerous_keywords:
            if f' {keyword} ' in f' {query_clean} ' or query_clean.startswith(f"{keyword} "):
                logger.warning(f"Blocked dangerous keyword: {keyword}")
                return False
        
        # Check for SQL injection patterns
        injection_patterns = [
            r'--',       # SQL comments
            r'/\*.*\*/', # Block comments
            r'@@\w+',    # System variables
            # Time-based attacks
            r'\b(?:SLEEP|BENCHMARK|PG_SLEEP|WAITFOR\s+DELAY|WAITFOR\s+TIME)\s*\('
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, query_clean, re.IGNORECASE):
                logger.warning(f"Blocked suspicious pattern: {pattern}")
                return False
        
        # Additional validation for SELECT statements
        if query_clean.startswith('SELECT'):
            # Check for UNION-based injection
            if re.search(r'\bUNION\s+SELECT\b', query_clean, re.IGNORECASE):
                logger.warning("Blocked UNION-based injection attempt")
                return False
                
            # Check for always true conditions (1=1, 'x'='x')
            if re.search(r'\b(?:OR|AND)\s+[\w\.]+\s*=\s*[\w\.]+(?:\s+OR\s+[\w\.]+\s*=\s*[\w\.]+)*\s*$', query_clean, re.IGNORECASE):
                logger.warning("Blocked potential always-true condition")
                return False
        
        return True

    def validate_sql(self, query: str) -> bool:
        """
        SQL validation is currently disabled.
        
        Args:
            query: SQL query to validate
            
        Returns:
            Always returns True (all queries are allowed)
        """
        logger.warning("SQL validation is currently disabled. All queries will be executed.")
        return True

    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute SQL query/queries and return results.
        
        Args:
            query: SQL query to execute (can contain multiple statements)
            params: Optional query parameters (only works with single statement)
            
        Returns:
            Dictionary containing query results and status
        """
        try:
            # Split into individual statements
            statements = [s.strip() for s in query.split(';') if s.strip()]
            
            # Validate all statements first
            if not self.validate_sql(query):
                return {
                    'status': 'error',
                    'message': 'Query validation failed - only safe DML operations are allowed',
                    'data': []
                }
            
            with self.get_connection() as conn:
                # Start a transaction
                trans = conn.begin()
                results = []
                
                try:
                    for stmt in statements:
                        # Skip empty statements
                        if not stmt:
                            continue
                            
                        # Execute the current statement
                        result = conn.execute(text(stmt), params or {})
                        
                        # For SELECT queries, fetch results
                        if stmt.strip().upper().startswith('SELECT'):
                            columns = list(result.keys())
                            data = [dict(zip(columns, row)) for row in result.fetchall()]
                            results.append({
                                'statement': stmt,
                                'data': data,
                                'rowcount': len(data)
                            })
                        else:
                            # For INSERT/UPDATE/DELETE, store rowcount
                            results.append({
                                'statement': stmt,
                                'rowcount': result.rowcount
                            })
                    
                    # If we got here, all statements executed successfully
                    trans.commit()
                    
                    # If there's only one statement, return a simple result
                    if len(results) == 1:
                        result = results[0]
                        return {
                            'status': 'success',
                            'message': 'Query executed successfully',
                            'data': result.get('data', []),
                            'rowcount': result.get('rowcount', 0)
                        }
                    else:
                        # For multiple statements, return all results
                        return {
                            'status': 'success',
                            'message': f'Executed {len(results)} statements successfully',
                            'statements': results,
                            'rowcount': sum(r.get('rowcount', 0) for r in results)
                        }
                except Exception as e:
                    # Rollback on any error
                    trans.rollback()
                    raise
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return {
                'status': 'error',
                'message': f'Error executing query: {str(e)}',
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