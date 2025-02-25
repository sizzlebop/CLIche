"""
OpenAI provider implementation
"""
import os
from typing import Dict, List, Tuple
from openai import OpenAI
from .base import LLMBase

class OpenAIProvider(LLMBase):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.client = OpenAI(api_key=config.get('api_key') or os.getenv('OPENAI_API_KEY'))

    async def generate_response(self, query: str, include_sys_info: bool = False, professional_mode: bool = False) -> str:
        try:                 
            # Get the configured model or use gpt-4o as default
            model = self.config.get('model', 'gpt-4o')
            
            response = self.client.chat.completions.create(
                model=model,  # Use the configured model
                messages=[
                    {"role": "system", "content": self.get_system_context(include_sys_info, professional_mode)},
                    {"role": "user", "content": query}
                ],
                max_tokens=self.config.get('max_tokens', 1000)  # Use our new default
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"OpenAI Error: {str(e)}"

    async def list_models(self) -> List[Tuple[str, str]]:
        """List available OpenAI models."""
        try:
            response = self.client.models.list()
            models = []
            for model in response.data:
                # Add O-series models and legacy models
                if any(model.id.startswith(prefix) for prefix in ['gpt-4o', 'gpt-40', 'gpt-o3', 'gpt-o1']):
                    if any(latest in model.id for latest in [
                        'gpt-4o',             
                        'gpt-4o-turbo',       
                        'gpt-4o-mini',        
                        'o3-mini',         
                        'o3-mini-high',    
                        'o1',              
                    ]):
                        description = {
                            'gpt-4o': "Great for most tasks",
                            'gpt-4o-turbo': "Faster version of gpt-4o",
                            'gpt-4o-mini': "Efficient version of gpt-4o",
                            'o3-mini': "Great at coding and logic",
                            'o3-mini-high': "Enhanced o3 model",
                            'o1': "Great at reasoning and research"
                        }.get(model.id, "O-series model")
                        models.append((model.id, description))
            return sorted(models)
        except Exception as e:
            return [("Error", f"Failed to fetch models: {str(e)}")]
