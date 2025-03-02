#!/usr/bin/env python3
"""
Development runner for CLIche.
Run this script directly from the development directory.
"""
import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Import the CLI directly without going through the entry point
from cliche.core import cli

# Simple helper to check if dependencies are installed
def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import requests
        import bs4
        import click
        import crawl4ai
        print("✅ Core dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

if __name__ == "__main__":
    print("\n🚀 CLIche Development Runner")
    print("─────────────────────────\n")
    
    # Check dependencies
    check_dependencies()
    
    if len(sys.argv) > 1:
        # Remove the script name from argv when invoking the CLI
        args = sys.argv[1:]
        print(f"Running: cliche {' '.join(args)}")
        print("─" * 40)
        # Run the CLI
        cli(args)
    else:
        print("Usage: ./run_cliche.py [command] [arguments...]")
        print("Example: ./run_cliche.py scrape https://python.org Python") 