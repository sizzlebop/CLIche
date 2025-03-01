"""
OpenRouter provider implementation
"""
import os
from typing import Dict, List, Tuple
import requests
from .base import LLMBase

class OpenRouterProvider(LLMBase):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.api_key = config.get('api_key') or os.getenv('OPENROUTER_API_KEY')
        self.api_base = "https://openrouter.ai/api/v1"

    async def generate_response(self, query: str, include_sys_info: bool = False, professional_mode: bool = False) -> str:
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://github.com/sizzlebop/cliche",  # Required by OpenRouter
                    "X-Title": "CLIche"  # Required by OpenRouter
                },
                json={
                    "model": self.config['model'],
                    "messages": [
                        {"role": "system", "content": self.get_system_context(include_sys_info, professional_mode)},
                        {"role": "user", "content": query}
                    ]
                }
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"OpenRouter Error: {str(e)}"

    async def list_models(self) -> List[Tuple[str, str]]:
        """List available OpenRouter models."""
        try:
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://github.com/sizzlebop/cliche",  # Required by OpenRouter
                    "X-Title": "CLIche"  # Required by OpenRouter
                }
            )
            response.raise_for_status()
            
            data = response.json()
            models = []
            for model in data.get('data', []):
                # Format pricing info
                prompt_price = float(model['pricing']['prompt']) * 1000  # Convert to per 1k tokens
                completion_price = float(model['pricing']['completion']) * 1000
                pricing = f"${prompt_price:.3f}/1k prompt, ${completion_price:.3f}/1k completion"
                
                description = (
                    f"{model.get('name', 'Unknown')} - "
                    f"Context: {model.get('context_length', 'Unknown')}, "
                    f"{pricing}"
                )
                models.append((model['id'], description))
            return sorted(models, key=lambda x: x[1]) if models else [("deepseek/deepseek-r1:free")]
        except Exception as e:
            print(f"Error fetching models: {str(e)}")  # Add error logging
            # Fallback to basic models if API fails
            return [
                ("deepseek/deepseek-r1:free"),
                ("cognitivecomputations/dolphin3.0-r1-mistral-24b:free"),
                ("meta-llama/llama-3.3-70b-instruct:free"),                
                ("asophosympatheia/rogue-rose-103b-v0.2:free"),
                ("gryphe/mythomax-l2-13b:free"),
                ("google/gemma-2-9b-it:free")
            ]
