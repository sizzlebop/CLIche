#!/usr/bin/env python3
"""
Setup script for CLIche bypass environment.
Creates a virtual environment for testing CLIche without Cursor's environment.
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

def print_step(msg):
    """Print a step message with formatting."""
    print(f"\n\033[1;36m=== {msg} ===\033[0m")

def run_command(cmd, shell=False):
    """Run a command and handle errors."""
    try:
        if shell:
            subprocess.run(cmd, shell=True, check=True)
        else:
            subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\033[1;31mCommand failed: {e}\033[0m")
        return False
    except Exception as e:
        print(f"\033[1;31mError: {e}\033[0m")
        return False

def main():
    """Main setup function."""
    # Get the project root directory
    project_root = Path.cwd()
    
    # Create the bypass environment directory
    env_dir = project_root / "cliche-bypass-env"
    if not env_dir.exists():
        print_step(f"Creating bypass environment at {env_dir}")
        env_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a Python virtual environment
    venv_dir = env_dir / "venv"
    if not venv_dir.exists():
        print_step("Creating Python virtual environment")
        if not run_command([sys.executable, "-m", "venv", str(venv_dir)]):
            print("Failed to create virtual environment. Please ensure Python venv module is installed.")
            return False
    
    # Determine the Python and pip executables in the virtual environment
    if platform.system() == "Windows":
        python_exe = venv_dir / "Scripts" / "python.exe"
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
        pip_exe = venv_dir / "bin" / "pip"
    
    # Upgrade pip
    print_step("Upgrading pip")
    run_command([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"])
    
    # Install required dependencies
    print_step("Installing dependencies")
    run_command([
        str(pip_exe), "install",
        "click", "rich", "requests", "beautifulsoup4", "aiohttp",
        "pydantic", "playwright", "lxml", "crawl4ai",
        "duckduckgo-search", "openai", "anthropic", "google-generativeai"
    ])
    
    # Install playwright browsers
    print_step("Installing Playwright browsers")
    run_command([str(python_exe), "-m", "playwright", "install", "chromium"])
    
    # Create .env file for API keys if it doesn't exist
    env_file = project_root / ".env"
    if not env_file.exists():
        print_step("Creating .env file template")
        with open(env_file, "w") as f:
            f.write("""# CLIche API Keys
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
DEEPSEEK_API_KEY=
OPENROUTER_API_KEY=
UNSPLASH_API_KEY=
BRAVE_API_KEY=
""")
        print("Created .env file. Please edit it to add your API keys.")
    
    # Create an activation script for the environment
    activate_script = project_root / "activate_bypass.sh"
    if platform.system() != "Windows":
        print_step("Creating activation script")
        with open(activate_script, "w") as f:
            f.write(f"""#!/bin/bash
# Activate the bypass environment
export PYTHONPATH="{project_root}:$PYTHONPATH"
source "{venv_dir}/bin/activate"
echo "CLIche bypass environment activated."
""")
        os.chmod(activate_script, 0o755)
    
    # Make the bypass script executable
    bypass_script = project_root / "cliche-bypass"
    if bypass_script.exists():
        print_step("Making bypass script executable")
        os.chmod(bypass_script, 0o755)
    
    print("\n\033[1;32m=== Setup completed successfully ===\033[0m")
    if platform.system() != "Windows":
        print(f"To activate the environment, run: source {activate_script}")
    else:
        print(f"To activate the environment, run: {venv_dir}\\Scripts\\activate")
    
    print("\nThen you can use the bypass script like this:")
    print("./cliche-bypass scrape \"https://python.org\"")
    return True

if __name__ == "__main__":
    main() 