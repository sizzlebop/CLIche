#!/bin/bash


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
echo -e "${CYAN}📦 Creating virtual environment...${WHITE}"
python3 -m venv /opt/cliche/venv

# Copy project files
echo -e "${CYAN}📂 Copying project files...${WHITE}"
cp -r cliche /opt/cliche/
cp setup.py /opt/cliche/
cp requirements.txt /opt/cliche/
cp environment.yml /opt/cliche/ 2>/dev/null || :
cp *.sh /opt/cliche/ 2>/dev/null || :
cp *.md /opt/cliche/ 2>/dev/null || :

# Install the package
echo -e "${CYAN}📦 Installing package dependencies...${WHITE}"
cd /opt/cliche
source venv/bin/activate
pip install --upgrade pip
pip install -e .

# Install image viewing dependencies
echo -e "${CYAN}🖼️ Setting up image viewing capabilities...${WHITE}"
# Set flag to indicate we're running from the installer
export CLICHE_INSTALLING=1
chmod +x install_image_deps.sh
./install_image_deps.sh
unset CLICHE_INSTALLING

# Create symlink to make cliche available system-wide
echo -e "${CYAN}🔗 Creating system-wide symlink...${WHITE}"
sudo ln -sf /opt/cliche/venv/bin/cliche /usr/local/bin/cliche

# Make uninstall script executable
chmod +x uninstall.sh && sudo cp uninstall.sh /opt/cliche/uninstall.sh

# Create config directory if it doesn't exist
echo -e "${CYAN}🔧 Setting up configuration...${WHITE}"
mkdir -p ~/.config/cliche

# Reload bashrc
source ~/.bashrc

# Test the installation
if command -v cliche >/dev/null 2>&1; then
    echo -e "    
                  ### #   #        #      ### #   #    #   ### # 
                ##  #   ##       ##     ##  #   ##   #   ##  #  
                ##       ##       ##    ##       ##   #  ##      
                ##       ##       ##    ##       ######  ####    
                ##       ##       ##    ##       ##   #  ##      
                ##   #   ##    #  ##    ##   #   ##   #  ##   #  
                ### ##   ###  #   #     ### ##   #    #  ### ##  
                #### # # #####  #       #### # #    ###  #### # 

                "
    echo -e "${GREEN}🎉 CLIche installed successfully!${WHITE}"
    echo -e "${CYAN}✨ You can now use 'cliche' from anywhere.${WHITE}"
    echo -e "${PURPLE}🔑 To get started, configure your API settings${WHITE}"
    echo -e "${WHITE}cliche config --provider --api-key or --model${WHITE}"
    echo -e "${WHITE}   * Example: --provider openai --api-key {your-openai-api-key}${WHITE}"
    echo -e "${WHITE}   * Example: --provider ollama --model llama3${WHITE}"
    echo -e "${PINK}📚 For options type 'cliche --help'${NC}"
    echo -e "${YELLOW}📡 For web research: try the 'research' command${NC}"
    echo -e "${YELLOW}🔍 For web scraping: try the 'scrape' command${NC}"
    echo -e "${YELLOW}📄 To uninstall, run: sudo /opt/cliche/uninstall.sh${WHITE}"

    # Make symlink executable
    sudo chmod +x /usr/local/bin/cliche
else
    echo -e "${RED}❌ Installation failed. Please check the error messages above.${NC}"
    exit 1
fi