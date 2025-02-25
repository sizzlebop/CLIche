"""
Google provider implementation
"""
import os
from typing import Dict, List, Tuple
import google.generativeai as genai
from .base import LLMBase

class GoogleProvider(LLMBase):
    def __init__(self, config: Dict):
        super().__init__(config)
        genai.configure(api_key=config.get('api_key') or os.getenv('GOOGLE_API_KEY'))

    async def generate_response(self, query: str, include_sys_info: bool = False, professional_mode: bool = False) -> str:
        try:
            model = genai.GenerativeModel(self.config['model'])
            response = model.generate_content([
                {"role": "system", "content": self.get_system_context(include_sys_info, professional_mode)},
                {"role": "user", "content": query}
            ])
            return response.text
        except Exception as e:
            return f"Google Error: {str(e)}"

    async def list_models(self) -> List[Tuple[str, str]]:
        """List available Google models."""
        try:
            models = [
                ("gemini-2.0-pro", "Most capable model, best for complex tasks"),
                ("gemini-2.0-vision", "Vision and text model"),
                ("gemini-2.0-pro-latest", "Latest Pro model (auto-updates)"),
                ("gemini-2.0-vision-latest", "Latest Vision model (auto-updates)"),
                ("gemini-2.0-flash", "Fast and efficient model"),
                ("gemini-2.0-flash-latest", "Latest Flash model (auto-updates)")
            ]
            return models
        except Exception as e:
            return [("Error", f"Failed to fetch models: {str(e)}")]
