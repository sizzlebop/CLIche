#!/bin/bash
# Script to install image viewing dependencies for CLIche

echo "✨ Installing image viewing dependencies for CLIche..."

# Check if this is running from install.sh
if [ -z "$CLICHE_INSTALLING" ]; then
  echo "🔍 Installing Python dependencies..."
  pip install -q Pillow python-magic
fi

# Function to check if command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to check chafa version
check_chafa_version() {
  # Get chafa version
  local version_str=$(chafa --version | head -n 1)
  local version=$(echo "$version_str" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
  local major=$(echo "$version" | cut -d. -f1)
  local minor=$(echo "$version" | cut -d. -f2)
  
  # Check if version is at least 1.12.0 (recommended)
  if [[ "$major" -gt 1 || ("$major" -eq 1 && "$minor" -ge 12) ]]; then
    echo "✅ chafa version $version is installed (recommended version 1.12.0+ detected)"
    return 0
  else
    echo "✅ chafa version $version is installed"
    echo "⚠️ Version 1.12.0+ is recommended for optimal image display. Consider upgrading."
    return 1
  fi
}

# Check for chafa (primary viewer)
if command_exists chafa; then
  echo "✅ chafa is already installed."
  
  # Check version and suggest upgrade if needed
  check_chafa_version
else
  echo "🔍 Installing chafa (terminal image viewer)..."
  
  # Get Ubuntu codename if on Ubuntu
  UBUNTU_CODENAME=""
  if [ -f /etc/lsb-release ]; then
    source /etc/lsb-release
    UBUNTU_CODENAME=$DISTRIB_CODENAME
  fi
  
  # Try OS-specific methods with best options for each distribution
  if command_exists apt-get; then
    # Debian/Ubuntu
    if [ "$UBUNTU_CODENAME" = "noble" ] || [ "$UBUNTU_CODENAME" = "jammy" ] || [ "$UBUNTU_CODENAME" = "lunar" ] || [ "$UBUNTU_CODENAME" = "mantic" ]; then
      echo "📦 Ubuntu $UBUNTU_CODENAME detected - using apt to install chafa"
      # For newer Ubuntu versions, just use the package from the main repository
      sudo apt-get install -y chafa
    else
      # For older Ubuntu versions, try the PPA
      if command_exists add-apt-repository; then
        echo "📦 Adding repository for latest chafa version..."
        sudo add-apt-repository -y ppa:hpjansson/chafa 2>/dev/null || {
          echo "⚠️ PPA addition failed, falling back to standard repository"
          sudo apt-get update -qq
          sudo apt-get install -y chafa
        }
        if [ $? -eq 0 ]; then
          sudo apt-get update -qq
          sudo apt-get install -y chafa
        fi
      else
        # Fallback if add-apt-repository isn't available
        sudo apt-get install -y chafa
      fi
    fi
  elif command_exists brew; then
    # macOS with Homebrew - Always gets latest version
    brew install chafa
  elif command_exists dnf; then
    # Fedora/RHEL - Try COPR if available
    if command_exists dnf copr; then
      echo "📦 Enabling repository for latest chafa version..."
      sudo dnf copr enable -y hpjansson/chafa 2>/dev/null || {
        echo "⚠️ COPR enablement failed, falling back to standard repository"
        sudo dnf install -y chafa
      }
      if [ $? -eq 0 ]; then
        sudo dnf install -y chafa
      fi
    else
      sudo dnf install -y chafa
    fi
  elif command_exists pacman; then
    # Arch Linux - Should get latest from main repos
    sudo pacman -S --noconfirm chafa
  elif command_exists apk; then 
    # Alpine Linux
    sudo apk add chafa
  else
    echo "❌ Could not automatically install chafa."
    echo "Please install manually for optimal image viewing:"
    echo "  - Ubuntu/Debian: sudo apt install chafa"
    echo "  - macOS: brew install chafa"
    echo "  - Fedora/RHEL: sudo dnf install chafa"
    echo "  - Arch Linux: sudo pacman -S chafa"
    echo "  - From source (recommended for latest version):"
    echo "    git clone https://github.com/hpjansson/chafa.git"
    echo "    cd chafa && ./autogen.sh && make && sudo make install"
  fi
fi

# Check if install was successful
if command_exists chafa; then
  echo "✅ chafa installed successfully!"
  # Check version 
  check_chafa_version
  
  # Version-specific recommendations
  if ! check_chafa_version; then
    echo "🔧 For optimal image display, version 1.12.0+ is recommended."
    echo "   Consider installing from source: https://github.com/hpjansson/chafa"
  fi
else
  echo "⚠️ chafa installation failed or not available for your system."
  
  # Check for fallback viewers
  echo "🔍 Checking for fallback viewers..."
  
  if command_exists jp2a; then
    echo "✅ jp2a is available for ASCII image viewing."
  else
    echo "🔍 Installing jp2a (ASCII image viewer fallback)..."
    if command_exists apt-get; then
      sudo apt-get install -y jp2a
    elif command_exists brew; then
      brew install jp2a
    elif command_exists dnf; then
      sudo dnf install -y jp2a
    elif command_exists pacman; then
      sudo pacman -S --noconfirm jp2a
    fi
  fi
  
  if command_exists img2sixel || [ -n "$TERM" ] && [[ "$TERM" == *"xterm"* ]]; then
    echo "✅ Sixel graphics support available."
  fi
  
  echo "ℹ️ For best results, please consider installing chafa from source:"
  echo "   git clone https://github.com/hpjansson/chafa.git"
  echo "   cd chafa && ./autogen.sh && make && sudo make install"
fi

echo "✨ Image viewing dependencies setup complete!"
echo "To generate and view an image, try:"
echo "  cliche image \"beautiful sunset over mountains\" --generate --view" 