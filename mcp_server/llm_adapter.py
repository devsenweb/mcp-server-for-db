"""
LLM Adapter for MCP Server

Author: devsen
"""

import requests
import json
import yaml
import os
from typing import Dict, Any, Optional

class LLMAdapter:
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)['llm']
        
        self.base_url = self.config['base_url']
        self.model = self.config['model']
    
    def generate_sql(self, prompt: str, schema: Dict[str, Any]) -> str:
        """Generate SQL from natural language prompt using the LLM."""
        system_prompt = """You are a helpful AI assistant that generates SQL queries based on the database schema and user requests.
        The database schema is provided below. Only respond with valid SQL, no explanations or markdown formatting.
        """
        
        schema_str = json.dumps(schema, indent=2)
        full_prompt = f"""Database Schema:
        {schema_str}
        
        User Request: {prompt}
        
        Respond with only the SQL query, no additional text or markdown formatting."""
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "system": system_prompt,
                    "stream": False,
                    "options": {"temperature": 0.1}
                }
            )
            response.raise_for_status()
            return response.json().get('response', '').strip()
        except Exception as e:
            raise Exception(f"Error generating SQL: {str(e)}")
