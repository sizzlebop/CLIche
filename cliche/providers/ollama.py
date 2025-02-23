"""
Ollama provider implementation
"""
import os
from typing import Dict
import requests
from .base import LLMBase

class OllamaProvider(LLMBase):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.host = config.get('host', 'http://localhost:11434')

    async def generate_response(self, query: str, include_sys_info: bool = False) -> str:
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.config['model'],
                    "system": self.get_system_context(include_sys_info),
                    "prompt": query,
                    "stream": False,
                    "options": {
                        "num_predict": self.config.get('max_tokens', 150)
                    }
                }
            )
            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            return f"Ollama Error: {str(e)}"