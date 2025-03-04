#!/usr/bin/env python3
"""
Config file manager for CLIche

This script ensures that a proper config.json file exists in the correct location.
If the file doesn't exist, it will create it with the default template structure.
If it exists, it will leave it untouched.
"""

import json
import os
from pathlib import Path

# Default configuration template
DEFAULT_CONFIG = {
  "providers": {
    "openai": {
      "api_key": "your_openai_key_here",
      "model": "gpt-3.5-turbo",
      "max_tokens": 16000
    },
    "anthropic": {
      "api_key": "your_anthropic_key_here",
      "model": "claude-instant",
      "max_tokens": 100000
    },
    "google": {
      "api_key": "your_google_key_here",
      "model": "gemini-pro",
      "max_tokens": 32000
    },
    "deepseek": {
      "api_key": "your_deepseek_key_here",
      "model": "deepseek-chat",
      "max_tokens": 8192,
      "api_base": "https://api.deepseek.com/v1"
    },
    "openrouter": {
      "api_key": "your_openrouter_key_here",
      "model": "openai/gpt-3.5-turbo",
      "max_tokens": 100000
    },
    "ollama": {
      "host": "http://localhost:11434",
      "model": "llama3",
      "max_tokens": 100000
    }
  }
}

def ensure_config_exists():
    """
    Ensure that the config file exists and has the proper structure.
    Returns True if the file was created, False if it already existed.
    """
    config_dir = Path.home() / ".config" / "cliche"
    config_path = config_dir / "config.json"
    
    # Create the directory if it doesn't exist
    if not config_dir.exists():
        print(f"Creating config directory: {config_dir}")
        config_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if the config file exists
    if config_path.exists():
        print(f"Config file already exists at {config_path}")
        return False
    
    # Create the config file with the default template
    with open(config_path, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
    
    print(f"Created default config file at {config_path}")
    print("Please update the file with your actual API keys.")
    return True

def backup_config():
    """
    Create a backup of the existing config file.
    Returns the path to the backup if successful, None otherwise.
    """
    config_path = Path.home() / ".config" / "cliche" / "config.json"
    if not config_path.exists():
        print("No config file to backup.")
        return None
    
    # Create a backup with timestamp
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config_path.with_suffix(f".backup_{timestamp}.json")
    
    try:
        import shutil
        shutil.copy2(config_path, backup_path)
        print(f"Created backup of config file at {backup_path}")
        return backup_path
    except Exception as e:
        print(f"Failed to create backup: {e}")
        return None

def main():
    """Main function to ensure config exists and is properly structured."""
    print("CLIche Config Manager")
    print("====================")
    
    # First, create a backup of any existing config
    backup_config()
    
    # Then ensure the config exists
    created = ensure_config_exists()
    
    if created:
        print("\nA new configuration file has been created.")
        print("Please edit it to add your API keys:")
        print(f"  nano {Path.home() / '.config' / 'cliche' / 'config.json'}")
    else:
        print("\nYour existing configuration file has been preserved.")
        print("You can edit it at any time:")
        print(f"  nano {Path.home() / '.config' / 'cliche' / 'config.json'}")

if __name__ == "__main__":
    main() 