
# 🗃️ MCP Server for Databases

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
- Support for multiple transport protocols (http, WebSocket, stdio)
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
python -m mcp_server.server --transport http --port 8080
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

## 🛠️ IDE and Tool Integration

### (Cursor IDE) .cursor/mcp.json
```json
{
  "mcpServers": {
    "database-query": {
      "url": "http://localhost:8000/mcp",
      "transport": "http"
    }
  }
}
```

### MCP Inspector
```bash
npm install -g @modelcontextprotocol/inspector
mcp-inspector --transport http --url http://localhost:8000/mcp
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
python -m mcp_server.server   --host 0.0.0.0   --port 8000   --transport http   --config ./config.yaml
```

---

## 🙏 Acknowledgments

- Powered by [SQLAlchemy](https://www.sqlalchemy.org/)
- Based on the Model Context Protocol (MCP) standard

## ⚠️ Disclaimer

This project is a **demo implementation** of an MCP-compatible server for database interaction. It does **not include SQL safety mechanisms**, input sanitization, authentication, or permission controls.

> ⚠️ **Use at your own risk.** This server executes raw SQL and is intended for experimentation, prototyping, and local development only.  
>  
> It is the responsibility of the user to implement proper **guardrails**, **validation**, and **security measures** before using this in any production or sensitive environment.
