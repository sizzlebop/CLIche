"""
Ollama provider implementation
"""
import os
from typing import Dict, List, Tuple
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
                        "num_predict": self.config.get('max_tokens', 300)
                    }
                }
            )
            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            return f"Ollama Error: {str(e)}"

    async def list_models(self) -> List[Tuple[str, str]]:
        """List available Ollama models."""
        try:
            response = requests.get(f"{self.host}/api/tags")
            response.raise_for_status()
            models = []
            for model in response.json().get('models', []):
                models.append((
                    model['name'],
                    f"Local model, size: {model.get('size', 'unknown')}"
                ))
            return sorted(models)
        except requests.exceptions.ConnectionError:
            return [("Error", "Failed to connect to Ollama server")]
        except Exception as e:
            return [("Error", f"Failed to fetch models: {str(e)}")]