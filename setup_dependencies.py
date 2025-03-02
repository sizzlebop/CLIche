#!/usr/bin/env python3
"""
Install required dependencies for testing the scraping module.
"""
import subprocess
import sys

def install_dependencies():
    """Install required packages."""
    print("📦 Installing required dependencies...")
    dependencies = [
        "click",
        "rich",
        "requests",
        "beautifulsoup4",
        "aiohttp",
        "pydantic",
        "lxml",
        "playwright",
        "duckduckgo-search"
    ]
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + dependencies)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
        
if __name__ == "__main__":
    install_dependencies() 