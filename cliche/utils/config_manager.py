#!/usr/bin/env python3
"""
Config file manager for CLIche

This script ensures that a proper config.json file exists in the correct location.
If the file doesn't exist, it will create it with the default template structure.
If it exists, it will leave it untouched.
"""

import json
import os
import sys
import logging
from pathlib import Path
import datetime
import shutil

# Set up logging
logger = logging.getLogger("cliche.config_manager")

# Default configuration template
DEFAULT_CONFIG = {
  "providers": {
    "openai": {
      "api_key": "your_openai_key_here",
      "model": "gpt-4-turbo",
      "max_tokens": 10000
    },
    "anthropic": {
      "api_key": "your_anthropic_key_here",
      "model": "claude-3-opus", 
      "max_tokens": 10000
    },
    "google": {
      "api_key": "your_google_key_here",
      "model": "gemini-pro",
      "max_tokens": 10000
    },
    "deepseek": {
      "api_key": "your_deepseek_key_here",
      "model": "deepseek-chat",
      "max_tokens": 2048,
      "api_base": "https://api.deepseek.com/v1"
    },
    "openrouter": {
      "api_key": "your_openrouter_key_here",
      "model": "anthropic/claude-3-opus",
      "max_tokens": 50000
    },
    "ollama": {
      "host": "http://localhost:11434",
      "model": "llama3",
        "max_tokens": 50000
        }
  }
}

def get_config_path():
    """Get the path to the config file."""
    return Path.home() / ".config" / "cliche" / "config.json"

def get_config_dir():
    """Get the path to the config directory."""
    return Path.home() / ".config" / "cliche"

def ensure_config_exists():
    """
    Ensure that the config file exists and has the proper structure.
    Returns True if the file was created, False if it already existed.
    """
    config_dir = get_config_dir()
    config_path = get_config_path()
    
    # Create the directory if it doesn't exist
    if not config_dir.exists():
        logger.info(f"Creating config directory: {config_dir}")
        config_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if the config file exists
    if config_path.exists():
        logger.info(f"Config file already exists at {config_path}")
        return False
    
    # Create the config file with the default template
    with open(config_path, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
    
    logger.info(f"Created default config file at {config_path}")
    return True

def backup_config():
    """
    Create a backup of the existing config file.
    Returns the path to the backup if successful, None otherwise.
    """
    config_path = get_config_path()
    if not config_path.exists():
        logger.info("No config file to backup.")
        return None
    
    # Create a backup with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config_path.with_suffix(f".backup_{timestamp}.json")
    
    try:
        shutil.copy2(config_path, backup_path)
        logger.info(f"Created backup of config file at {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return None

def load_config():
    """
    Load the configuration from the config file.
    If the file doesn't exist, create it with the default template.
    """
    # Ensure the config file exists
    ensure_config_exists()
    
    # Load the config
    config_path = get_config_path()
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return DEFAULT_CONFIG

def save_config(config):
    """
    Save the configuration to the config file.
    Creates a backup of the existing file first.
    """
    # Create a backup first
    backup_config()
    
    # Save the config
    config_path = get_config_path()
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Saved config to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        return False

def main():
    """Main function when the module is run as a script."""
    # Configure logging to output to console
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s"
    )
    
    print("CLIche Config Manager")
    print("====================")
    
    # First, create a backup of any existing config
    backup = backup_config()
    if backup:
        print(f"Created backup of existing config at {backup}")
    
    # Then ensure the config exists
    created = ensure_config_exists()
    
    if created:
        print("\nA new configuration file has been created.")
        print("Please edit it to add your API keys:")
        print(f"  nano {get_config_path()}")
    else:
        print("\nYour existing configuration file has been preserved.")
        print("You can edit it at any time:")
        print(f"  nano {get_config_path()}")

# Automatically ensure config exists when the module is imported
# This will create the config file if it doesn't exist
ensure_config_exists()

if __name__ == "__main__":
    main() 