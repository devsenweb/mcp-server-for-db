"""
MCP Server for Database Operations

Author: devsen
"""

from fastmcp import FastMCP
from typing import Dict, Any, List, Optional
import asyncio
import logging
import yaml
from pathlib import Path

from .db_adapter import DatabaseAdapter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPServer:
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the MCP Server.
        
        Args:
            config_path: Path to config file. If None, uses default config.yaml in project root.
        """
        # Initialize FastMCP
        self.mcp = FastMCP("Database Query MCP Server")
        
        # Initialize database adapter with config
        try:
            self.db = DatabaseAdapter(config_path=config_path)
            logging.info(f"Connected to database: {self.db.db_uri}")
            logging.info(f"Database type: {self.db.engine.dialect.name}")
            logging.info(f"Tables found: {len(self.db.metadata.tables)}")
        except Exception as e:
            logging.error(f"Failed to initialize database: {e}")
            raise
        
        # Register tools, resources, and prompts
        self._register_tools()
        self._register_resources()
        self._register_prompts()
    
    def _register_tools(self):
        """Register MCP tools."""
        
        @self.mcp.tool()
        async def execute_query(sql: str) -> Dict[str, Any]:
            """Execute a SQL query directly against the database.
            
            Args:
                sql: SQL query to execute
                
            Returns:
                Dictionary containing query results and metadata
            """
            try:
                logger.info(f"Executing SQL: {sql}")
                result = await self._execute_query_async(sql)
                result['status'] = 'success'
                logger.info("Query executed successfully")
                return result
                
            except Exception as e:
                logger.error(f"Error executing query: {str(e)}")
                return {
                    'status': 'error', 
                    'message': str(e),
                    'data': []
                }
        
        @self.mcp.tool()
        async def validate_sql(sql: str) -> Dict[str, Any]:
            """Validate SQL query syntax and structure.
            
            Args:
                sql: SQL query to validate
                
            Returns:
                Dictionary containing validation results
            """
            try:
                is_valid = await self._validate_sql_async(sql)
                return {
                    'status': 'success',
                    'sql': sql,
                    'is_valid': is_valid,
                    'message': 'SQL is valid' if is_valid else 'SQL contains errors'
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'sql': sql,
                    'is_valid': False,
                    'message': str(e)
                }
    
    def _register_resources(self):
        """Register MCP resources."""
        
        @self.mcp.resource("db://schema")
        async def get_schema() -> Dict[str, Any]:
            """Get database schema information."""
            try:
                schema = await self._get_schema_async()
                return {
                    'status': 'success',
                    'schema': schema,
                    'database': {
                        'type': self.db.engine.dialect.name,
                        'uri': str(self.db.engine.url)  # Mask password in production
                    },
                    'timestamp': asyncio.get_event_loop().time()
                }
            except Exception as e:
                logger.error(f"Error getting schema: {str(e)}")
                return {
                    'status': 'error',
                    'message': str(e),
                    'schema': {}
                }
        
        @self.mcp.resource("db://tables")
        async def get_tables() -> Dict[str, Any]:
            """Get list of available database tables."""
            try:
                tables = await self._get_tables_async()
                return {
                    'status': 'success',
                    'tables': tables,
                    'count': len(tables)
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': str(e),
                    'tables': []
                }
    
    def _register_prompts(self):
        """Register MCP prompts with helpful database information."""
        
        @self.mcp.prompt("sql-tips")
        async def get_sql_tips() -> str:
            """
            Get SQL query writing tips for the connected database.
            """
            db_type = self.db.engine.dialect.name
            
            tips = {
                'sqlite': [
                    "Use `LIKE` for case-insensitive text matching with % wildcards",
                    "Remember to use `IS NULL` instead of `= NULL` for null checks",
                    "SQLite uses dynamic typing - columns can store any data type"
                ],
                'postgresql': [
                    "Use `ILIKE` for case-insensitive pattern matching",
                    "Use `::type` for type casting (e.g., `'2023-01-01'::date`)",
                    "Use `DISTINCT ON` for getting distinct rows based on specific columns"
                ],
                'mysql': [
                    "Use backticks (`) to quote identifiers with special characters",
                    "Use `IFNULL()` or `COALESCE()` for handling NULL values",
                    "`GROUP BY` behavior is less strict than in other databases"
                ],
                'mssql': [
                    "Use `TOP` instead of `LIMIT` for result limiting",
                    "Use `ISNULL()` or `COALESCE()` for handling NULL values",
                    "String concatenation uses + operator"
                ]
            }
            
            common_tips = [
                "Always use parameterized queries to prevent SQL injection",
                "Use `EXPLAIN` to analyze query performance",
                "Index columns used in WHERE, JOIN, and ORDER BY clauses",
                "Use transactions for multiple related operations",
                "Avoid SELECT * - specify only needed columns"
            ]
            
            db_specific = tips.get(db_type, [])
            all_tips = common_tips + db_specific
            
            return (
                f"# SQL Tips for {db_type.upper()}\n\n" +
                "## General Tips\n" +
                "\n".join(f"- {tip}" for tip in common_tips) +
                "\n\n## Database-Specific Tips\n" +
                "\n".join(f"- {tip}" for tip in db_specific)
            )
        
        @self.mcp.prompt("example-queries")
        async def get_example_queries() -> str:
            """
            Get example SQL queries for the connected database.
            """
            tables = await self._get_tables_async()
            
            if not tables:
                return "No tables found in the database to generate example queries."
                
            examples = [
                f"-- Get all columns from a table\nSELECT * FROM {tables[0]} LIMIT 10;\n",
                f"-- Count rows in a table\nSELECT COUNT(*) AS row_count FROM {tables[0]};\n",
                "-- Find tables with specific column names\n"
                "SELECT table_name, column_name, data_type \n"
                "FROM information_schema.columns \n"
                "WHERE column_name LIKE '%name%' OR column_name LIKE '%id%';\n",
                "-- Find tables with their row counts\n"
                "SELECT table_name, table_rows \n"
                "FROM information_schema.tables \n"
                f"WHERE table_schema = '{self.db.engine.url.database}';"
            ]
            
            if len(tables) > 1:
                examples.append(
                    f"-- Join two tables\n"
                    f"SELECT a.*, b.* \n"
                    f"FROM {tables[0]} a \n"
                    f"JOIN {tables[1]} b ON a.id = b.{tables[0]}_id\n"
                    f"LIMIT 10;"
                )
            
            return "## Example SQL Queries\n\n" + "\n".join(examples)
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the connected database."""
        return {
            'database_type': self.db.engine.dialect.name,
            'database_name': self.db.engine.url.database,
            'username': self.db.engine.url.username,
            'host': self.db.engine.url.host,
            'port': self.db.engine.url.port,
            'tables_count': len(self.db.metadata.tables)
        }
    
    async def _execute_query_async(self, sql: str) -> Dict[str, Any]:
        """Execute SQL query asynchronously."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.db.execute_query, sql
        )

    async def _validate_sql_async(self, sql: str) -> bool:
        """Async wrapper for SQL validation."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.db.validate_sql, sql)
    
    async def _get_schema_async(self) -> Dict[str, Any]:
        """Async wrapper for getting database schema."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.db.get_schema)
    
    async def _get_tables_async(self) -> List[str]:
        """Async wrapper for getting database tables."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.db.get_tables)
    
    def run(self, host: str = "0.0.0.0", port: int = 8080, transport: str = "stdio"):
        """Run the MCP server.
        
        Args:
            host: Host to bind to (for HTTP transports)
            port: Port to bind to (for HTTP transports)
            transport: Transport type ("stdio", "sse", or "ws")
        """
        try:
            logger.info(f"Starting MCP server with transport: {transport}")
            
            if transport == "stdio":
                # For stdio transport (most common for MCP)
                self.mcp.run()
            elif transport == "sse":
                # For Server-Sent Events HTTP transport
                self.mcp.run(transport="sse", host=host, port=port)
            elif transport == "ws":
                # For WebSocket transport
                self.mcp.run(transport="ws", host=host, port=port)
            else:
                raise ValueError(f"Unsupported transport: {transport}")
                
        except Exception as e:
            logger.error(f"Failed to start server: {str(e)}")
            raise

def load_config(config_path: Optional[str] = None) -> dict:
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / 'config.yaml'
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
        
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

# Create server instance
config = load_config()
server = MCPServer()

if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run MCP Database Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--transport', default='http', choices=['http', 'ws', 'sse'],
                       help='Transport protocol to use')
    
    # Override with config values if not specified in command line
    args = parser.parse_args()
    server_config = config.get('server', {})
    
    # Start the server using MCP's run method
    server.run(
        host=server_config.get('host', args.host),
        port=server_config.get('port', args.port),
        transport=server_config.get('transport', args.transport)
    )