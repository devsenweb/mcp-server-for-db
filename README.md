
# 🗃️ Database MCP Server

![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)

A lightweight implementation of the **Model Context Protocol (MCP)** for database operations. This server enables AI models to interact with SQL databases through a structured, tool-based interface, providing safe and efficient database access.

---

## 📚 Table of Contents

- [🚀 Key Capabilities](#-key-capabilities)
- [🔧 Getting Started](#-getting-started)
- [🧠 MCP Interface](#-mcp-interface)
- [🤖 MCP Client Integration](#-mcp-client-integration)
- [🧩 LLM Integration](#-llm-integration)
- [❗ Error Handling](#-error-handling)
- [🛠️ IDE and Tool Integration](#-ide-and-tool-integration)
- [⚙️ Development](#-development)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [⚙️ MCP Server Configuration Reference](#-mcp-server-configuration-reference)
- [🙏 Acknowledgments](#-acknowledgments)

---

## 🚀 Key Capabilities

### 🛠️ MCP Tool Integration
- Exposes database operations as MCP tools for AI model interaction
- Supports natural language prompts for database exploration
- Provides schema-aware query building assistance

### 💾 Database Support
- Works with any SQLAlchemy-compatible database (SQLite, PostgreSQL, MySQL, etc.)
- Automatic schema inspection and reflection
- Transaction support for multi-statement operations

### 📡 MCP Features
- Native MCP tools, resources, and prompts
- Support for multiple transport protocols (SSE, WebSocket, stdio)
- Structured error handling and validation

---

## 🔧 Getting Started

### ✅ Prerequisites
- Python 3.8+
- SQLite or any other SQLAlchemy-supported database

### ⚙️ Installation

```bash
git clone https://github.com/devsenweb/mcp-server-for-db.git
cd mcp-server-for-db
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 🛠️ Configuration

Edit `config.yaml`:

```yaml
db:
  uri: sqlite:///./example.db  # Supports any SQLAlchemy URI
```

(Optional) Create a sample DB:

```bash
python create_database.py
```

### ▶️ Starting the MCP Server

```bash
python -m mcp_server.server --transport sse --port 8080
# or
python -m mcp_server.server --transport ws --port 8080
# or
python -m mcp_server.server --transport stdio
```

---

## 🧠 MCP Interface

### 📌 Tool Definitions

#### `execute_query`
```json
{
  "jsonrpc": "2.0",
  "method": "tools/execute_query",
  "params": {
    "sql": "SELECT * FROM users WHERE age > 25"
  },
  "id": 1
}
```

#### `validate_sql`
```json
{
  "jsonrpc": "2.0",
  "method": "tools/validate_sql",
  "params": {
    "sql": "SELECT * FROM users"
  },
  "id": 2
}
```

---

### 📁 Resource Endpoints

#### `db://schema`
```json
{
  "jsonrpc": "2.0",
  "method": "resources/get",
  "params": {
    "uri": "db://schema"
  },
  "id": 3
}
```

#### `db://tables`
```json
{
  "jsonrpc": "2.0",
  "method": "resources/get",
  "params": {
    "uri": "db://tables"
  },
  "id": 4
}
```

---

## 🤖 MCP Client Integration

### 🐍 Python Example

```python
from mcp.client import MCPClient
import asyncio

async def query_database():
    async with MCPClient("http://localhost:8080") as client:
        schema = await client.resources.get("db://schema")
        result = await client.tools.execute_query(
            sql="SELECT * FROM users WHERE age > 25"
        )
        tips = await client.prompts.get("sql-tips")
        return {
            "schema": schema,
            "results": result,
            "tips": tips
        }

response = asyncio.run(query_database())
```

---

## 🧩 LLM Integration

### Example with OpenAI

```python
from mcp.client import MCPClient
from openai import OpenAI

async def query_with_llm(natural_language_query: str):
    async with MCPClient("http://localhost:8000") as client:
        schema = await client.resources.get("db://schema")
        llm = OpenAI()
        system_prompt = f"You are a database expert. Given the schema: {schema}..."
        response = await llm.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": natural_language_query}
            ]
        )
        sql_query = response.choices[0].message.content
        return await client.tools.execute_query(sql=sql_query)
```

---

## ❗ Error Handling

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32603,
    "message": "Database connection failed",
    "data": {
      "details": "Connection refused to localhost:5432"
    }
  },
  "id": "unique-request-id"
}
```

---

## 🛠️ IDE and Tool Integration

### VSCode (Cursor IDE)
```json
{
  "mcpServers": {
    "database-query": {
      "url": "http://localhost:8000/sse",
      "transport": "sse"
    }
  }
}
```

### MCP Inspector
```bash
npm install -g @modelcontextprotocol/inspector
mcp-inspector --transport sse --url http://localhost:8000/sse
# Visit http://localhost:3000
```

---

## ⚙️ Development

```bash
pip install -r requirements-dev.txt
pytest tests/
```

### 📁 Project Structure

```
mcp-server-for-db/
├── mcp_server/
│   ├── __init__.py
│   ├── server.py
│   └── db_adapter.py
├── config.yaml
├── create_database.py
└── requirements.txt
```

---

## 🤝 Contributing

Contributions are welcome! Feel free to submit a Pull Request.

---

## 📄 License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## ⚙️ MCP Server Configuration Reference

```bash
python -m mcp_server.server   --host 0.0.0.0   --port 8000   --transport sse   --config ./config.yaml
```

---

## 🙏 Acknowledgments

- Powered by [SQLAlchemy](https://www.sqlalchemy.org/)
- Based on the Model Context Protocol (MCP) standard
