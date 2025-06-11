"""
MCP Server for Database Operations

Author: devsen
"""

from fastmcp import FastMCP
from typing import Dict, Any
import asyncio
import logging

from .db_adapter import DatabaseAdapter
from .llm_adapter import LLMAdapter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPServer:
    def __init__(self):
        """Initialize the MCP server with FastMCP."""
        # Initialize FastMCP directly (no FastAPI needed)
        self.mcp = FastMCP("Database Query MCP Server")
        
        # Initialize adapters
        self.db = DatabaseAdapter()
        self.llm = LLMAdapter()
        
        # Option 1: Simple logging right after initialization

        # Now this should work - db_uri is available in the attributes
        logging.info(f"Database URI: {self.db.db_uri}")
        logging.info(f"Database Type: {self.db.engine.dialect.name}")
        logging.info(f"Tables Found: {len(self.db.metadata.tables)}")
        
         # Log LLM configuration (assuming your LLMAdapter loads from config too)
        logging.info(f"LLM Provider: {getattr(self.llm, 'provider', 'N/A')}")
        logging.info(f"LLM Model: {getattr(self.llm, 'model', 'N/A')}")
        logging.info(f"LLM Base URL: {getattr(self.llm, 'base_url', 'N/A')}")
        # Register tools, resources, and prompts
        self._register_tools()
        self._register_resources()
        self._register_prompts()
    
    def _register_tools(self):
        """Register MCP tools."""
        
        @self.mcp.tool()
        async def db_query(prompt: str) -> Dict[str, Any]:
            """Execute a database query based on natural language prompt.
            
            Args:
                prompt: Natural language description of the desired query
                
            Returns:
                Dictionary containing query results and metadata
            """
            try:
                logger.info(f"Processing query: {prompt}")
                
                # Get schema and generate SQL
                schema = await self._get_schema_async()
                sql = await self._generate_sql_async(prompt, schema)
                
                # Execute query
                result = await self._execute_query_async(sql)
                result['generated_sql'] = sql
                result['status'] = 'success'
                
                logger.info(f"Query executed successfully: {sql}")
                return result
                
            except Exception as e:
                logger.error(f"Error processing query: {str(e)}")
                return {
                    'status': 'error', 
                    'message': str(e),
                    'generated_sql': None,
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
                    'tables': tables
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': str(e),
                    'tables': []
                }
    
    def _register_prompts(self):
        """Register MCP prompts."""
        
        @self.mcp.prompt("sample-queries")
        async def sample_queries() -> str:
            """Get sample database query prompts."""
            return """Here are some sample database queries you can try:

• Show all users who registered in the last 7 days
• List all orders with status 'pending' 
• Get average salary per department
• Insert a new product named 'Widget 2.0' priced at $49
• Delete all logs older than 30 days
• Find customers who haven't placed orders in the last 30 days
• Show top 10 products by sales volume
• Get monthly revenue totals for the current year
• List all employees hired in 2024
• Find duplicate email addresses in the users table"""
        
        @self.mcp.prompt("schema-help")
        async def schema_help() -> str:
            """Get help with database schema and structure."""
            try:
                schema = await self._get_schema_async()
                
                schema_info = "Database Schema:\n"
                for table, info in schema.items():
                    schema_info += f"\n{table}:\n"
                    if 'columns' in info:
                        for col in info['columns']:
                            schema_info += f"  - {col}\n"
                
                # Try to get tables if method exists
                try:
                    tables = await self._get_tables_async()
                    schema_info = f"Available tables: {', '.join(tables)}\n\n" + schema_info
                except AttributeError:
                    # get_tables method doesn't exist, skip it
                    pass
                
                return schema_info
            except Exception as e:
                return f"Error retrieving schema: {str(e)}"
        
        @self.mcp.prompt("query-tips")
        async def query_tips() -> str:
            """Get tips for writing effective database queries."""
            return """Tips for effective database queries:

🔍 **Query Structure:**
• Use specific column names instead of SELECT *
• Always include WHERE clauses to limit results
• Use LIMIT to prevent large result sets

📊 **Aggregations:**
• Use GROUP BY with aggregate functions (COUNT, SUM, AVG)
• HAVING filters groups, WHERE filters rows
• ORDER BY for sorting results

⚡ **Performance:**
• Index frequently queried columns
• Avoid functions in WHERE clauses
• Use EXISTS instead of IN for subqueries

🛡️ **Safety:**
• Always validate input parameters
• Use prepared statements to prevent SQL injection
• Test queries on small datasets first

💡 **Common Patterns:**
• JOIN tables using foreign key relationships
• Use CASE statements for conditional logic
• Subqueries for complex filtering"""

    async def _get_schema_async(self) -> Dict[str, Any]:
        """Async wrapper for getting database schema."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.db.get_schema)
    
    async def _generate_sql_async(self, prompt: str, schema: Dict[str, Any]) -> str:
        """Async wrapper for generating SQL."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.llm.generate_sql, prompt, schema)
    
    async def _execute_query_async(self, sql: str) -> Dict[str, Any]:
        """Async wrapper for executing database query."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.db.execute_query, sql)
    
    async def _validate_sql_async(self, sql: str) -> bool:
        """Async wrapper for SQL validation."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.db.validate_sql, sql)
    
    async def _get_tables_async(self) -> list:
        """Async wrapper for getting table list."""
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

# Create server instance
server = MCPServer()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run MCP Database Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--transport", default="stdio", 
                       choices=["stdio", "sse", "ws"],
                       help="Transport type")
    
    args = parser.parse_args()
    
    server.run(host=args.host, port=args.port, transport=args.transport)