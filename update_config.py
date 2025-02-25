#!/usr/bin/env python3
"""
Update CLIche configuration file with correct DeepSeek model name
"""

import json
from pathlib import Path

def update_config():
    """Update the CLIche config file with the correct DeepSeek model name."""
    config_path = Path.home() / ".config" / "cliche" / "config.json"
    
    if not config_path.exists():
        print(f"Config file not found at {config_path}")
        return False
    
    # Load existing config
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return False
    
    # Check if DeepSeek provider exists
    if "providers" not in config:
        print("No providers section found in config")
        return False
    
    if "deepseek" not in config["providers"]:
        print("No DeepSeek provider found in config")
        return False
    
    # Update model name
    old_model = config["providers"]["deepseek"].get("model", "")
    config["providers"]["deepseek"]["model"] = "deepseek-chat"
    
    # Save updated config
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"Updated DeepSeek model name from '{old_model}' to 'deepseek-chat'")
        print(f"Configuration saved to {config_path}")
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

if __name__ == "__main__":
    success = update_config()
    print("\nConfiguration update", "successful" if success else "failed") 