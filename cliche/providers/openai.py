"""
OpenAI provider implementation
"""
import os
from typing import Dict
from openai import OpenAI
from .base import LLMBase

class OpenAIProvider(LLMBase):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.client = OpenAI(api_key=config.get('api_key') or os.getenv('OPENAI_API_KEY'))

    async def generate_response(self, query: str, include_sys_info: bool = False) -> str:
        try:                 
            response = self.client.chat.completions.create(
                model=self.config['model'],
                messages=[
                    {"role": "system", "content": self.get_system_context(include_sys_info)},
                    {"role": "user", "content": query}
                ],
                max_tokens=self.config.get('max_tokens', 150)
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"OpenAI Error: {str(e)}"
