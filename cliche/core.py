"""
Core functionality for CLIche CLI tool
"""
import json
import os
import click
from pathlib import Path
from typing import Dict
from enum import Enum
from .providers.openai import OpenAIProvider
from .providers.anthropic import AnthropicProvider
from .providers.google import GoogleProvider
from .providers.ollama import OllamaProvider

class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"

class Config:
    def __init__(self):
        self.config_dir = Path.home() / '.config' / 'cliche'
        self.config_file = self.config_dir / 'config.json'
        self.config = self.load_config()

    def load_config(self) -> Dict:
        if not self.config_file.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
            return self.get_default_config()
        
        with open(self.config_file) as f:
            return json.load(f)

    def get_default_config(self) -> Dict:
        default_config = {
            "active_provider": "openai",
            "providers": {
                "openai": {
                    "api_key": "",
                    "model": "gpt-4",
                    "max_tokens": 150
                },
                "anthropic": {
                    "api_key": "",
                    "model": "claude-3.5-sonnet",
                    "max_tokens": 150
                },
                "google": {
                    "api_key": "",
                    "model": "gemini-2.0-flash"
                },
                "deepseek": {
                    "api_key": "",
                    "model": "deepseek-chat"
                },
                "openrouter": {
                    "api_key": "",
                    "model": "openrouter/auto"
                },
                "ollama": {
                    "host": "http://localhost:11434",
                    "model": "Llama3.2:3b"
                }
            },
            "personality": "snarky, witty, encyclopedic, slightly sarcastic, helpful, knowledgeable"
        }
        self.save_config(default_config)
        return default_config

    def save_config(self, config: Dict) -> None:
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def get_provider_config(self, provider: str) -> Dict:
        return self.config["providers"].get(provider, {})

class CLIche:
    def __init__(self):
        self.config = Config()
        self.provider = self._get_provider()

    def _get_provider(self):
        provider_name = self.config.config["active_provider"]
        provider_config = self.config.get_provider_config(provider_name)

        if provider_name == LLMProvider.OPENAI:
            return OpenAIProvider(provider_config)
        elif provider_name == LLMProvider.ANTHROPIC:
            return AnthropicProvider(provider_config)
        elif provider_name == LLMProvider.GOOGLE:
            return GoogleProvider(provider_config)
        elif provider_name == LLMProvider.OLLAMA:
            return OllamaProvider(provider_config)
        else:
            raise ValueError(f"Unsupported provider: {provider_name}")

    async def ask_llm(self, query: str, include_sys_info: bool = False) -> str:
        """Ask the LLM a question.
        
        Args:
            query: The question to ask
            include_sys_info: Whether to include system information in the context
        """
        return await self.provider.generate_response(query, include_sys_info)

@click.group()
def cli():
    """CLIche: Your terminal's snarky genius assistant"""
    pass
