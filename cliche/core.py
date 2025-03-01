"""
Core functionality for CLIche
"""
import os
import json
import click
from pathlib import Path
from enum import Enum
from typing import Optional, Dict, Any

from .providers.openai import OpenAIProvider
from .providers.anthropic import AnthropicProvider
from .providers.google import GoogleProvider
from .providers.ollama import OllamaProvider
from .providers.deepseek import DeepSeekProvider
from .providers.openrouter import OpenRouterProvider
from .utils.generate_from_scrape import generate

class Config:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "cliche"
        self.config_file = self.config_dir / "config.json"
        self.config = self._load_config()
        self._load_services_env()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_file.exists():
            # Create default config
            default_config = {
                "provider": "openai",
                "providers": {
                    "openai": {"api_key": "", "model": "gpt-4"},
                    "anthropic": {"api_key": "", "model": "claude-3-opus-20240229"},
                    "google": {"api_key": "", "model": "gemini-pro"},
                    "ollama": {"model": "phi4"},
                    "deepseek": {"api_key": "", "model": "deepseek-chat"},
                    "openrouter": {"api_key": "", "model": "gpt-4-turbo-preview"}
                },
                "services": {
                    "unsplash": {"api_key": ""},
                    "stability_ai": {"api_key": ""},
                    "dalle": {"use_openai_key": False},
                    "brave_search": {"api_key": ""}
                },
                "image_generation": {
                    "default_provider": "dalle",  # Options: dalle, stability
                    "default_size": "1024x1024",
                    "default_quality": "standard"  # Options: standard, hd
                }
            }
            self.save_config(default_config)
            return default_config

        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            click.echo("Error reading config file. Using defaults.")
            return {"provider": "openai", "providers": {}, "services": {}}

    def _load_services_env(self) -> None:
        """Load service API keys into environment variables."""
        # Load Unsplash API key if configured
        if 'services' in self.config and 'unsplash' in self.config['services']:
            unsplash_key = self.config['services']['unsplash'].get('api_key')
            if unsplash_key:
                os.environ['UNSPLASH_API_KEY'] = unsplash_key
        
        # Load Stability AI key if configured
        if 'services' in self.config and 'stability_ai' in self.config['services']:
            stability_key = self.config['services']['stability_ai'].get('api_key')
            if stability_key:
                os.environ['STABILITY_API_KEY'] = stability_key
        
        # Handle DALL-E configuration (uses OpenAI key)
        if 'services' in self.config and 'dalle' in self.config['services']:
            use_openai_key = self.config['services']['dalle'].get('use_openai_key')
            if use_openai_key:
                # Get the OpenAI key
                openai_key = self.config.get('providers', {}).get('openai', {}).get('api_key')
                if openai_key:
                    # Make it available to DALL-E utilities
                    os.environ['OPENAI_API_KEY'] = openai_key

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Write config file
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=4)
        
        self.config = config
        # Reload service API keys
        self._load_services_env()

    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """Get configuration for a specific provider."""
        return self.config.get("providers", {}).get(provider_name, {})

class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    DEEPSEEK = "deepseek"
    OPENROUTER = "openrouter"

def get_llm():
    """Get the configured LLM provider."""
    cliche = CLIche()
    return cliche.provider

class CLIche:
    def __init__(self):
        self.config = Config()
        self.provider = self._get_provider()

    def _get_provider(self):
        """Get the configured LLM provider."""
        provider_name = self.config.config.get("provider", "openai").lower()
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
            raise ValueError(f"Unknown provider: {provider_name}")

    def _should_include_system_info(self, query: str) -> bool:
        """Determine if system information should be included based on query content."""
        system_keywords = [
            "system", "os", "platform", "hardware", "cpu", "memory",
            "ram", "disk", "storage", "network", "gpu", "processor"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in system_keywords)

    def ask_llm(self, query: str):
        """Ask the LLM a question.
        
        Args:
            query: The question to ask
        """
        return self.provider.generate_response(query)

# Create the main CLI group
@click.group()
def cli():
    """CLIche: Your terminal's snarky genius assistant"""
    pass

# Register commands
def register_all_commands():
    from .commands.registry import register_commands
    register_commands(cli)

register_all_commands()
