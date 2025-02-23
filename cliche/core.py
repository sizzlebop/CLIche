"""
Core functionality for CLIche CLI tool
"""
import json
import os
import click
from pathlib import Path
from typing import Dict, Any
from enum import Enum
from dotenv import load_dotenv
from .providers.openai import OpenAIProvider
from .providers.anthropic import AnthropicProvider
from .providers.google import GoogleProvider
from .providers.ollama import OllamaProvider
from .providers.deepseek import DeepSeekProvider
from .providers.openrouter import OpenRouterProvider

class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    DEEPSEEK = "deepseek"
    OPENROUTER = "openrouter"

class Config:
    def __init__(self):
        # Load environment variables from .env file
        env_path = Path.home() / ".config" / "cliche" / ".env"
        load_dotenv(env_path)
        
        self.config_dir = Path.home() / ".config" / "cliche"
        self.config_file = self.config_dir / "config.json"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file and environment variables."""
        default_config = {
            "active_provider": "openai",
            "providers": {
                "openai": {
                    "api_key": os.getenv("OPENAI_API_KEY", ""),
                    "model": "gpt-4o",
                    "max_tokens": 150
                },
                "anthropic": {
                    "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
                    "model": "claude-3.5-sonnet-20240307",
                    "max_tokens": 150
                },
                "google": {
                    "api_key": os.getenv("GOOGLE_API_KEY", ""),
                    "model": "gemini-2.0-flash"
                },
                "deepseek": {
                    "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                    "model": "deepseek-chat"
                },
                "openrouter": {
                    "api_key": os.getenv("OPENROUTER_API_KEY", ""),
                    "model": "openrouter/auto"
                },
                "ollama": {
                    "host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
                    "model": "Llama3.2:3b"
                }
            },
            "personality": "snarky, witty, encyclopedic, slightly sarcastic, helpful, knowledgeable"
        }

        if not self.config_file.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.save_config(default_config)
            return default_config

        try:
            with open(self.config_file) as f:
                config = json.load(f)
                # Update API keys from environment if available
                for provider, settings in config["providers"].items():
                    env_key = f"{provider.upper()}_API_KEY"
                    if provider == "ollama":
                        if os.getenv("OLLAMA_HOST"):
                            settings["host"] = os.getenv("OLLAMA_HOST")
                    elif os.getenv(env_key):
                        settings["api_key"] = os.getenv(env_key)
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return default_config

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

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
        elif provider_name == LLMProvider.DEEPSEEK:
            return DeepSeekProvider(provider_config)
        elif provider_name == LLMProvider.OPENROUTER:
            return OpenRouterProvider(provider_config)
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
