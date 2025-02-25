#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[38;5;14m'
YELLOW='\033[38;5;11m'
NC='\033[0m' # No Color

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${YELLOW}Uninstalling CLIche...${NC}"

# Remove symlink
echo -e "${CYAN}Removing CLIche symlink...${NC}"
if ! rm -f /usr/local/bin/cliche; then
    echo -e "${RED}Failed to remove CLIche symlink${NC}"
    exit 1
fi

# Remove installation directory
echo -e "${CYAN}Removing CLIche installation directory...${NC}"
if ! rm -rf /opt/cliche; then
    echo -e "${RED}Failed to remove CLIche installation directory${NC}"
    exit 1
fi

# Note: We do not remove user data and configurations
echo -e "${CYAN}Note: Your personal data and configurations in ~/.cliche/ and ~/.config/cliche/ have been preserved.${NC}"
echo -e "${CYAN}To remove them as well, run: rm -rf ~/.cliche ~/.config/cliche${NC}"

echo -e "${GREEN}✨ CLIche has been uninstalled successfully.${NC}"