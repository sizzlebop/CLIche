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
        if 'api_key' not in config:
            raise ValueError("DeepSeek API key not found in config")
        self.api_key = config['api_key']
        self.api_base = "https://api.deepseek.com/v1"

    async def generate_response(self, query: str, include_sys_info: bool = False, professional_mode: bool = False) -> str:
        try:
            api_url = f"{self.api_base}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.config['model'],
                "messages": [
                    {"role": "system", "content": self.get_system_context(include_sys_info, professional_mode)},
                    {"role": "user", "content": query}
                ],
                "max_tokens": self.config.get('max_tokens', 50000),
                "temperature": 0.7
            }
            
            response = requests.post(
                api_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                error_detail = f"Status: {response.status_code}, Response: {response.text}"
                return f"💡 DeepSeek Error: {response.status_code} - {response.reason}. Details: {response.text}"
                
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"💡 DeepSeek Error: {str(e)}"

    async def list_models(self) -> List[Tuple[str, str]]:
        """List available DeepSeek models."""
        models = [
            ("deepseek-chat", "General purpose chat model"),
            ("deepseek-coder", "Code-specialized model"),
        ]
        return models
