"""
LLM provider implementations
"""
from enum import Enum
from .base import LLMBase
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .google import GoogleProvider
from .ollama import OllamaProvider
from .deepseek import DeepSeekProvider
from .openrouter import OpenRouterProvider

class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    DEEPSEEK = "deepseek"
    OPENROUTER = "openrouter"

def get_provider_class(provider_name: str):
    """Get a provider class by name."""
    provider_name = provider_name.lower()
    
    if provider_name == LLMProvider.OPENAI.value:
        return OpenAIProvider
    elif provider_name == LLMProvider.ANTHROPIC.value:
        return AnthropicProvider
    elif provider_name == LLMProvider.GOOGLE.value:
        return GoogleProvider
    elif provider_name == LLMProvider.OLLAMA.value:
        return OllamaProvider
    elif provider_name == LLMProvider.DEEPSEEK.value:
        return DeepSeekProvider
    elif provider_name == LLMProvider.OPENROUTER.value:
        return OpenRouterProvider
    else:
        return None

__all__ = [
    'LLMBase', 
    'LLMProvider', 
    'OpenAIProvider', 
    'AnthropicProvider', 
    'GoogleProvider', 
    'OllamaProvider', 
    'DeepSeekProvider', 
    'OpenRouterProvider',
    'get_provider_class'
]
