"""
Core functionality for CLIche CLI tool
"""
import json
import os
import re
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
        self.config_dir = Path.home() / ".config" / "cliche"
        self.config_file = self.config_dir / "config.json"
        self.env_file = self.config_dir / ".env"
        
        # Always ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create .env from template if it doesn't exist
        if not self.env_file.exists():
            template_path = Path(__file__).parent / ".env.template"
            if template_path.exists():
                import shutil
                shutil.copy(template_path, self.env_file)
                click.echo("✨ Created .env file at ~/.config/cliche/.env")
                click.echo("   Please add your API keys there.")
        
        # Load environment variables from .env file
        load_dotenv(self.env_file)
        
        # Load or create config
        self.config = self._load_config()
        
        # Always save config to ensure it exists with latest defaults
        self.save_config(self.config)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file and environment variables."""
        default_config = {
            "active_provider": "openai",
            "providers": {
                "openai": {
                    "model": "gpt-4o",
                    "max_tokens": 1000
                },
                "anthropic": {
                    "model": "claude-3.5-sonnet-20240307",
                    "max_tokens": 1000
                },
                "google": {
                    "model": "gemini-2.0-flash",
                    "max_tokens": 1000
                },
                "deepseek": {
                    "model": "deepseek-chat-v1",
                    "max_tokens": 1000
                },
                "openrouter": {
                    "model": "meta-llama/llama-3.3-70b-instruct:free",
                    "max_tokens": 1000
                },
                "ollama": {
                    "host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
                    "model": "phi4",
                    "max_tokens": 1000
                }
            }
        }

        if not self.config_file.exists():
            click.echo("✨ Created default config at ~/.config/cliche/config.json")
            return default_config

        try:
            with open(self.config_file) as f:
                config = json.load(f)
                return self._migrate_config(config)
        except Exception as e:
            click.echo(f"Error loading config: {e}. Using defaults.")
            return default_config

    def _migrate_config(self, config: Dict) -> Dict:
        """Migrate old config format to new format."""
        # Remove personality field if it exists
        if "personality" in config:
            del config["personality"]
            click.echo("✨ Removed legacy personality field from config")
        
        # Move API keys to .env if they exist in config
        moved_keys = []
        for provider, settings in config["providers"].items():
            if "api_key" in settings:
                # Write to .env file
                with open(self.env_file, "a") as f:
                    f.write(f"\n{provider.upper()}_API_KEY={settings['api_key']}")
                del settings["api_key"]  # Remove from config
                moved_keys.append(provider)
        
        if moved_keys:
            click.echo(f"✨ Moved API keys to .env for: {', '.join(moved_keys)}")
        
        # Remove llamacpp if it exists (not supported anymore)
        if "llamacpp" in config["providers"]:
            del config["providers"]["llamacpp"]
            click.echo("✨ Removed unsupported llamacpp provider")
        
        # Save the cleaned config
        self.save_config(config)
        return config

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        # Format config with sections
        formatted_config = {
            # Active provider section
            "active_provider": config["active_provider"],
            
            # Provider settings section
            "providers": config["providers"]
        }
        
        # Save with nice formatting (indentation and newlines)
        with open(self.config_file, "w") as f:
            json.dump(formatted_config, f, indent=4, sort_keys=False)

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

    def _should_include_system_info(self, query: str) -> bool:
        """Determine if system information should be included based on query content."""
        # Keywords that suggest system-related queries
        system_keywords = [
            'system', 'cpu', 'memory', 'ram', 'disk', 'storage', 'gpu', 'processor',
            'hardware', 'os', 'operating system', 'linux', 'windows', 'mac',
            'process', 'running', 'load', 'usage', 'performance', 'monitor',
            'status', 'resource', 'uptime', 'version', 'install', 'update',
            'config', 'configuration', 'setting', 'driver', 'device',
            'mount', 'unmount', 'service', 'systemctl', 'daemon',
            'network', 'interface', 'port', 'connection', 'bandwidth',
            'kill', 'terminate', 'restart', 'shutdown', 'reboot',
            'log', 'error', 'warning', 'debug', 'trace',
            'permission', 'access', 'user', 'group', 'sudo'
        ]
        
        # Create a regex pattern that matches whole words only
        pattern = r'\b(?:' + '|'.join(system_keywords) + r')\b'
        
        # Check if query contains any system-related keywords
        return bool(re.search(pattern, query.lower()))

    async def ask_llm(self, query: str) -> str:
        """Ask the LLM a question.
        
        Args:
            query: The question to ask
        """
        # Automatically determine if we should include system info
        include_sys_info = self._should_include_system_info(query)
        return await self.provider.generate_response(query, include_sys_info)

def get_llm():
    """Get the current LLM instance."""
    cliche = CLIche()
    return cliche.provider

@click.group()
def cli():
    """CLIche: Your terminal's snarky genius assistant"""
    pass
