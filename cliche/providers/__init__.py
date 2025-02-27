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

__all__ = [
    'LLMBase', 
    'LLMProvider', 
    'OpenAIProvider', 
    'AnthropicProvider', 
    'GoogleProvider', 
    'OllamaProvider', 
    'DeepSeekProvider', 
    'OpenRouterProvider'
]
