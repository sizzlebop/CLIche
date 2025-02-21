#!/bin/bash

# Create an alias in ~/.bashrc if it doesn't exist
if ! grep -q "alias cliche=" ~/.bashrc; then
    echo "Adding cliche alias to ~/.bashrc..."
    echo "alias cliche=\"$PWD/venv/bin/cliche\"" >> ~/.bashrc
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
PURPLE='\033[0;34m'
PINK='\033[38;5;13m'
CYAN='\033[38;5;14m'
YELLOW='\033[38;5;11m'
WHITE='\033[38;5;15m'
NC='\033[0m' # No Color

echo -e "${PINK}🔧 Installing CLIche...${WHITE}"

# Create virtual environment in /opt/cliche if it doesn't exist
if [ ! -d "/opt/cliche" ]; then
    echo -e "${PURPLE}📝 Creating installation directory...${WHITE}"
    sudo mkdir -p /opt/cliche
    sudo chown $USER:$USER /opt/cliche
fi

# Create and activate virtual environment
python3 -m venv /opt/cliche/venv

# Copy project files
cp -r cliche /opt/cliche/
cp setup.py /opt/cliche/
cp requirements.txt /opt/cliche/

# Install the package
cd /opt/cliche
source venv/bin/activate
pip install -e .

# Create symlink to make cliche available system-wide
sudo ln -sf /opt/cliche/venv/bin/cliche /usr/local/bin/cliche

# Make uninstall script executable
chmod +x uninstall.sh && sudo cp uninstall.sh /opt/cliche/uninstall.sh

# Reload bashrc
source ~/.bashrc

# Test the installation
if command -v cliche >/dev/null 2>&1; then
    echo -e "${GREEN}🎉 CLIche installed successfully!${WHITE}"
    echo -e "${CYAN}✨ You can now use 'cliche' from anywhere.${WHITE}"
    echo -e "${PURPLE}🔑 To get started, configure your API settings${WHITE}"
    echo -e "${WHITE}cliche config --provider --api-key or --model${WHITE}"
    echo -e "${WHITE}   * Example: --provider openai --api-key {your-openai-api-key}${WHITE}"
    echo -e "${WHITE}   * Example: --provider ollama --model LLama3.2:3b${WHITE}"
    echo -e "${PINK}📚 For options type 'cliche --help'"
    echo -e "${YELLOW}To uninstall, run: /opt/cliche/uninstall.sh${WHITE}"

        # Make symlink executable
    sudo chmod +x /usr/local/bin/cliche
else
    echo -e "${RED}❌ Installation failed. Please check the error messages above.${NC}"
    exit 1
fi

# Reload shell to update PATH
exec $SHELL