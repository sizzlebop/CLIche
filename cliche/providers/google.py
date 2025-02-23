"""
Google provider implementation
"""
import os
from typing import Dict
import google.generativeai as genai
from .base import LLMBase

class GoogleProvider(LLMBase):
    def __init__(self, config: Dict):
        super().__init__(config)
        genai.configure(api_key=config.get('api_key') or os.getenv('GOOGLE_API_KEY'))
        self.model = genai.GenerativeModel(self.config['model'])

    async def generate_response(self, query: str, include_sys_info: bool = False) -> str:
        try:
            response = self.model.generate_content(
                [
                    {"role": "system", "content": self.get_system_context(include_sys_info)},
                    {"role": "user", "content": query}
                ],
                generation_config={"max_output_tokens": self.config.get('max_tokens', 150)}
            )
            return response.text
        except Exception as e:
            return f"Google AI Error: {str(e)}"
