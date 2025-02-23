"""
Anthropic provider implementation
"""
import os
from typing import Dict
import anthropic
from .base import LLMBase

class AnthropicProvider(LLMBase):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.client = anthropic.Anthropic(api_key=config.get('api_key') or os.getenv('ANTHROPIC_API_KEY'))

    async def generate_response(self, query: str, include_sys_info: bool = False) -> str:
        try:
            response = self.client.messages.create(
                model=self.config['model'],
                messages=[
                    {"role": "system", "content": self.get_system_context(include_sys_info)},
                    {"role": "user", "content": query}
                ],
                max_tokens=self.config.get('max_tokens', 150)
            )
            return response.content[0].text
        except Exception as e:
            return f"Anthropic Error: {str(e)}"
