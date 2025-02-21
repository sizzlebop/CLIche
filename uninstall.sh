#!/bin/bash

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

echo "Uninstalling CLIche..."

# Remove symlink
if ! rm -f /usr/local/bin/cliche; then
    echo "Failed to remove CLIche symlink"
    exit 1
fi

# Remove installation directory
if ! rm -rf /opt/cliche; then
    echo "Failed to remove CLIche installation directory"
    exit 1
fi

echo "✨ CLIche has been uninstalled successfully."