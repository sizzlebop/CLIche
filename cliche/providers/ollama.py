"""
Ollama provider implementation
"""
import os
from typing import Dict, List, Tuple
import requests
from .base import LLMBase

class OllamaProvider(LLMBase):
    def __init__(self, config):
        """Initialize the Ollama provider."""
        
        # Check if config is a Config object or a dictionary
        if hasattr(config, 'get_provider_config'):
            # Config object
            provider_config = config.get_provider_config('ollama')
        else:
            # Dictionary
            provider_config = config
        
        # Get configuration values with proper defaults
        self.base_url = provider_config.get('host', 'http://localhost:11434')
        self.model = provider_config.get('model', 'llama3')
        self.max_tokens = provider_config.get('max_tokens', 2048)
        # Rest of initialization...

    async def generate_response(self, query: str, include_sys_info: bool = False, professional_mode: bool = False) -> str:
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "system": self.get_system_context(include_sys_info, professional_mode),
                    "prompt": query,
                    "stream": False,
                    "options": {
                        "num_predict": self.max_tokens
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
            response = requests.get(f"{self.base_url}/api/tags")
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