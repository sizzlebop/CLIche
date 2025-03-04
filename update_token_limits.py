#!/usr/bin/env python3
"""
Update Token Limits Script for CLIche

This script updates only the max_tokens values in the config file
while preserving all other settings (API keys, models, etc.)
"""
import json
import os
from pathlib import Path

# New token limits to apply - based on provider cost and limitations
NEW_TOKEN_LIMITS = {
    "openai": 20000,        # Set to ~20K as requested
    "anthropic": 20000,     # Set to ~20K as requested
    "google": 64000,        # Set higher since it's cheap/free
    "deepseek": 8192,       # Kept as is due to model limitations
    "openrouter": 100000,   # Kept at 100K as requested
    "ollama": 100000        # Set high since these are local models
}

def get_config_path():
    """Get the path to the config file."""
    return Path.home() / ".config" / "cliche" / "config.json"

def update_token_limits():
    """Update token limits in the config file."""
    config_path = get_config_path()
    
    # Check if config exists
    if not config_path.exists():
        print(f"Error: Config file not found at {config_path}")
        return False
    
    # Create backup
    backup_path = config_path.with_suffix(f".bak")
    try:
        import shutil
        shutil.copy2(config_path, backup_path)
        print(f"Created backup at {backup_path}")
    except Exception as e:
        print(f"Warning: Failed to create backup: {e}")
    
    # Load existing config
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error reading config file: {e}")
        return False
    
    # Update token limits
    if "providers" in config:
        updated = False
        for provider, new_limit in NEW_TOKEN_LIMITS.items():
            if provider in config["providers"]:
                # Only update max_tokens, preserve other settings
                config["providers"][provider]["max_tokens"] = new_limit
                updated = True
                print(f"Updated {provider} token limit to {new_limit}")
        
        if not updated:
            print("No provider settings found to update")
            return False
    else:
        print("Error: No 'providers' section found in config")
        return False
    
    # Save updated config
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"Successfully updated token limits in {config_path}")
        return True
    except Exception as e:
        print(f"Error saving config file: {e}")
        return False

if __name__ == "__main__":
    print("CLIche Token Limit Updater")
    print("==========================")
    print("This will update the max_tokens values in your config while preserving all other settings.")
    print("Token limits are customized based on provider costs and capabilities:")
    print("- OpenAI & Anthropic: ~20K tokens (balanced)")
    print("- Google: 64K tokens (higher since it's cheaper)")
    print("- DeepSeek: 8192 tokens (model limit)")
    print("- OpenRouter: 100K tokens")
    print("- Ollama: 100K tokens (local models)")
    
    if update_token_limits():
        print("\nSuccess! Your token limits have been updated.")
        print("You can verify the changes with: cliche config-manager --show")
    else:
        print("\nFailed to update token limits. Please check the error messages above.") 