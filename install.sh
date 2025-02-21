#!/bin/bash

echo "🚀 Installing CLIche..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install pip if not installed
python -m ensurepip --upgrade
python -m pip install --upgrade pip

# Install package in development mode
echo "Installing CLIche..."
pip install -e .

# Create config directory
CONFIG_DIR="$HOME/.config/cliche"
mkdir -p "$CONFIG_DIR"

# Create initial config.json if it doesn't exist
if [ ! -f "$CONFIG_DIR/config.json" ]; then
    echo "Creating default configuration..."
    cat > "$CONFIG_DIR/config.json" << EOF
{
  "active_provider": "openai",
  "providers": {
    "openai": {
      "api_key": "",
      "model": "gpt-4o",
      "max_tokens": 150
    },
    "anthropic": {
      "api_key": "",
      "model": "claude-3.5-sonnet"
    },
    "google": {
      "api_key": "",
      "model": "gemini-2.0-flash"
    },
    "deepseek": {
      "api_key": "",
      "model": "deepseek-chat"
    },
    "openrouter": {
      "api_key": "",
      "model": "openrouter/auto"
    }
  },
  "personality": "snarky"
}
EOF
fi

# Create an alias in ~/.bashrc if it doesn't exist
if ! grep -q "alias cliche=" ~/.bashrc; then
    echo "Adding cliche alias to ~/.bashrc..."
    echo "alias cliche=\"$PWD/venv/bin/cliche\"" >> ~/.bashrc
fi

echo "✨ Installation complete! To start using CLIche:"
echo "1. Run: source ~/.bashrc"
echo "2. Configure your API key:"
echo "   cliche config --provider openai --api-key your-api-key"
echo ""
echo "📚 Examples:"
echo "   cliche ask \"What is the meaning of life?\""
echo "   cliche roastme"
echo "   cliche ansi"