#!/usr/bin/env python3
"""
Fully standalone DeepSeek API test script
This doesn't depend on any CLIche package files.
"""

import os
import sys
import json
import requests
from pathlib import Path

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60 + "\n")

def load_config():
    """Load configuration from ~/.config/cliche/config.json."""
    config_path = Path.home() / ".config" / "cliche" / "config.json"
    
    if not config_path.exists():
        print(f"Config file not found at {config_path}")
        return None
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def test_deepseek_api():
    """Test the DeepSeek API using config from config file."""
    print_header("DeepSeek API Test")
    
    # Load configuration
    print("Loading configuration...")
    config = load_config()
    
    if not config:
        print("Failed to load configuration.")
        return False
    
    # Get DeepSeek settings
    deepseek_config = config.get("providers", {}).get("deepseek", {})
    
    # Check if DeepSeek is configured
    if not deepseek_config:
        print("DeepSeek provider not found in config.")
        return False
    
    # Get API key
    api_key = deepseek_config.get("api_key", "")
    if not api_key or api_key == "your_deepseek_key_here":
        print("DeepSeek API key not set properly in config.")
        return False
    
    # Get API base and model
    api_base = deepseek_config.get("api_base", "https://api.deepseek.com/v1")
    
    # Fixed model name - using deepseek-chat which is always available
    model = "deepseek-chat"
    
    print(f"Using API base: {api_base}")
    print(f"Using model: {model}")
    print(f"API key: ***{api_key[-4:] if len(api_key) > 4 else '****'}")
    
    # Build the API request
    url = f"{api_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, this is a test of the DeepSeek API. Please respond with a very short greeting."}
        ],
        "max_tokens": 50,  # Keep the response short
        "temperature": 0.7
    }
    
    # Print the full request for debugging
    print("\nRequest URL:", url)
    print("Request Headers:", {k: (v if k != 'Authorization' else '***') for k, v in headers.items()})
    print("Request Payload:", json.dumps(payload, indent=2))
    
    # Make the API call
    print("\nSending request to DeepSeek API...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            print("\nSuccess! Response:")
            print("-" * 30)
            print(content)
            print("-" * 30)
            
            # Display more details about the response
            usage = result.get("usage", {})
            if usage:
                print(f"\nToken Usage:")
                print(f"  Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
                print(f"  Completion tokens: {usage.get('completion_tokens', 'N/A')}")
                print(f"  Total tokens: {usage.get('total_tokens', 'N/A')}")
            
            return True
        else:
            print(f"\nError: Received status code {response.status_code}")
            print(f"Response: {response.text}")
            
            # Suggest fixes based on error message
            if "Model Not Exist" in response.text:
                print("\nSuggested fix: The model name in your config is incorrect.")
                print("DeepSeek's available models include: deepseek-chat, deepseek-coder")
                print("You should update your config at: ~/.config/cliche/config.json")
            
            return False
    except Exception as e:
        print(f"\nException occurred: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_deepseek_api()
    sys.exit(0 if success else 1) 