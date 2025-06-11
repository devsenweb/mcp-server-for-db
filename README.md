# MCP Server for Database Operations

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Model-Controller-Presenter (MCP) server that provides a natural language interface for database operations using LLM-powered SQL generation.

## ✨ Features

- **Natural Language to SQL**: Convert plain English queries into SQL
- **Multiple Database Support**: Works with any SQLAlchemy-supported database
- **LLM Integration**: Uses Ollama with CodeLlama model for SQL generation
- **RESTful API**: Built with FastMCP for easy integration
- **Schema Awareness**: Automatically understands your database structure
- **Safe SQL Validation**: Built-in protection against dangerous queries

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) running locally with CodeLlama model
- SQLite (or any other SQLAlchemy-supported database)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/devsenweb/mcp-server-for-db.git
   cd mcp-server-for-db
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   # or
   source .venv/bin/activate  # On macOS/Linux
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your database in `config.yaml`:
   ```yaml
   db:
     uri: sqlite:///./example.db  # Update with your database URI
   llm:
     provider: ollama
     base_url: http://localhost:11434
     model: codellama:7b  # Or your preferred model
   ```

5. Create a sample database (optional):
   ```bash
   python create_database.py
   ```

### Running the Server

Start the MCP server:
```bash
python -m mcp_server.server
```

## 📚 API Documentation

### Endpoints

- `POST /db_query` - Execute a natural language query
  ```json
  {
    "prompt": "Show all users who registered in the last 7 days"
  }
  ```

- `GET /db/schema` - Get database schema
- `GET /db/tables` - List all tables in the database
- `POST /validate_sql` - Validate SQL query syntax

### Example Usage

```python
import requests

# Natural language query
response = requests.post("http://localhost:8080/db_query", json={
    "prompt": "Show me the top 5 highest paid employees"
})
print(response.json())
```

## 🛠️ Development

### Project Structure

```
mcp-server-for-db/
├── mcp_server/
│   ├── __init__.py
│   ├── server.py         # Main server implementation
│   ├── db_adapter.py     # Database interaction layer
│   └── llm_adapter.py    # LLM integration
├── config.yaml           # Configuration file
├── create_database.py    # Sample database setup
└── requirements.txt      # Python dependencies
```

### Environment Setup

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run tests:
   ```bash
   pytest tests/
   ```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastMCP](https://github.com/yourusername/fastmcp)
- Uses [Ollama](https://ollama.ai/) for LLM capabilities
- Powered by [SQLAlchemy](https://www.sqlalchemy.org/)