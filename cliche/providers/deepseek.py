"""
DeepSeek provider implementation
"""
import os
from typing import Dict, List, Tuple
import requests
from .base import LLMBase

class DeepSeekProvider(LLMBase):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.api_key = config.get('api_key') or os.getenv('DEEPSEEK_API_KEY')
        self.api_base = "https://api.deepseek.com/v1"

    async def generate_response(self, query: str, include_sys_info: bool = False) -> str:
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.config['model'],
                    "messages": [
                        {"role": "system", "content": self.get_system_context(include_sys_info)},
                        {"role": "user", "content": query}
                    ],
                    "max_tokens": self.config.get('max_tokens', 1000),  # Use our new default
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"DeepSeek Error: {str(e)}"

    async def list_models(self) -> List[Tuple[str, str]]:
        """List available DeepSeek models."""
        models = [
            ("deepseek-chat-v1", "General purpose chat model"),
            ("deepseek-chat-v1-32k", "Extended context chat model (32k)"),
            ("deepseek-coder-v1", "Code-specialized model"),
            ("deepseek-coder-v1-32k", "Extended context code model (32k)"),
            ("deepseek-math-v1", "Mathematics-specialized model"),
            ("deepseek-research-v1", "Research and academic writing model")
        ]
        return models
