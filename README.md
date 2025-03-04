# CLIche

<div align="center">
  <img src="https://res.cloudinary.com/di7ctlowx/image/upload/v1740506249/Untitled_design_5_nielz6.png" alt="CLIche Logo" width="300"/>
  
  🤖 CLIche is a command-line interface for interacting with various LLM providers. It provides powerful web research capabilities, targeted scraping, and professional document generation. Snarky responses included at no extra charge.
</div>

### Turn your terminal into a wise-cracking genius with a snarky, all-knowing LLM assistant. Plus, gain the power to research topics, scrape websites, and generate professional documents.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

## Latest Features

### Interactive ANSI Art Drawing

- 🎨 **New `draw` Command**: Create ASCII and ANSI art with a full-featured terminal-based drawing editor
- 🖌️ **Rich Drawing Tools**: Block selection, line drawing, fill tools, and brush tools
- 🎬 **Animation Support**: Create frame-by-frame animations with customizable playback controls
- 🎭 **Multiple Drawing Modes**: Choose between ASCII text art or colorful ANSI block art with 256 colors
- 🖱️ **Mouse Support**: Intuitive mouse-based drawing interface with multiple tools

```bash
# Start the drawing editor
cliche draw

# Create ASCII text art
cliche draw --ascii

# Create colorful ANSI block art
cliche draw --ansi

# Set a custom canvas size
cliche draw -w 100 -h 40
```

### Enhanced Web Scraping & Research

- **Deep Content Extraction**: Extract up to 1 million characters from websites with the `scrape` command
- **Improved Link Following**: Configurable depth levels and page limits for more precise crawling
- **Content Prioritization**: Enhanced algorithm to extract larger, more relevant content chunks
- **Multiple Page Handling**: Better processing of content from linked pages within the same domain
- **Improved Debug Output**: Clear, detailed information about the scraping process and configuration
- **Improved Research**: Get up to 100,000 characters per page with the `research` command
```bash
# Scrape a website deeply (follow links 3 levels deep, max 5 pages total)
cliche scrape https://docs.python.org/3/library/asyncio.html --depth 3 --max-pages 5

# Research a topic with more comprehensive results
cliche research "machine learning techniques" --depth 5 --write
```

- 🖌️ **AI Image Generation**: Create images with DALL-E and Stability AI directly from the terminal
- 🎨 **Creative Control**: Select models, styles, and quality settings for your generated images
- 🤖 **AI-Powered Image Placement**: Intelligent contextual placement of images in documents based on content analysis
- 🔍 **Multiple Search Engines**: Added Brave Search integration alongside DuckDuckGo for more reliable web research
- 📂 **Automatic Unique File Naming**: Generate multiple documents on the same topic without overwriting previous files
- 🖼️ **Direct Image URLs**: Unsplash images are now embedded with direct URLs for better sharing and compatibility
- 📚 **Advanced Document Generation**: Intelligent chunking for comprehensive documents with the option for concise summaries
- 🔍 **Web Research**: Get up-to-date information from the web with `research` command
- 🕸️ **Web Scraping**: Extract and save content from websites with `scrape` command
- 📝 **Document Generation**: Create professional documents from scraped or researched data
- 🎭 **Personality Switching**: Snarky at it's core but professional when you need it
- 🔎 **File Search**: Find files on your computer with the `search` command

## Core Features

- 🎨 **Creative tools**:
  - Interactive ASCII/ANSI art editor with the `draw` command
  - ASCII text art and banner generation
  - ANSI color art creation
  - Animation capabilities
  
- 🔄 **Multi-provider support**:
  - OpenAI
  - Anthropic
  - Google
  - DeepSeek
  - OpenRouter - has many free models
  - Ollama - for using local models

- 🎯 **Easy provider switching**
- 🔐 **Secure API key management**
- 📝 **Rich configuration options**
- 🔥 **Get roasted by the AI**
- 😏 **Snarky responses included at no extra charge**
- 🔍 **File Search**: Find files on your computer with the `search` command
- 🔍 **Web Research**: Get up-to-date information from the web with `research` command
- 🕸️ **Web Scraping**: Extract and save content from websites with `scrape` command
- 📝 **Document Generation**: Create professional documents from scraped data
- 🖼️ **Image Features**:
  - Search and download from Unsplash with direct URLs
  - Generate AI images with DALL-E and Stability AI
  - Set model, style, quality, and size preferences
  - View all options with convenient --list-models and --list-styles
- 🎨 **Art & ANSI support**:
  - Generate ASCII text art with custom fonts
  - Display random ASCII art patterns
  - Display random ANSI art patterns
  - Create banner-style text headers


- ✨ **Base commands**:
  - `ask`: Ask the AI a question
  - `roastme`: Get roasted by the AI
  - `art`: Display random ASCII art patterns
  - `ansi`: Display random ANSI art patterns
  - `create`: Unified command for ASCII/ANSI art creation
  - `view`: View a generated file
  - `config`: Configure your API keys and model settings
  - `config-manager`: Manage CLIche configuration files
- 📝 **Generation commands**:
  - `code`: Generate code in any language.
  - `write`: Generate text, markdown, or HTML content
  - `research`: Search the web and generate responses based on current information. Generate documents from research with --write.
  - `scrape`: Extract and save web content
  - `generate`: Create documents from scraped content.
  - `view`: View a generated file
  - `image`: Search and download images from Unsplash
- 🔍 **System commands**:
  - `search`: Find files on your computer by name or type
  - `system`: Display system information
  - `servers`: List and manage running servers
  - `kill`: Kill a running server or process by PID

## Installation

### Quick Install (Recommended)

```bash
git clone https://github.com/pinkpixel-dev/cliche.git
cd cliche
sudo ./install.sh  # sudo is required for proper installation
```

> **Note**: The installation requires sudo privileges, especially for the drawing capabilities. The installation script will prompt for your password as needed.

### Manual Installation (Advanced Users)

```bash
# Clone the repository
git clone https://github.com/pinkpixel-dev/cliche.git
cd cliche

# Create a virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Install optional dependencies for image viewing
# For Ubuntu/Debian:
sudo apt install chafa libmagic1

# For macOS:
brew install chafa libmagic
```

Note that manual installation may not fully set up all dependencies for the `draw` command, which requires additional permissions to install properly.

## Terminal Image Viewing Dependencies

CLIche offers streamlined image viewing directly in your terminal with minimal output dialog. When generating or viewing images, the system:

- Automatically detects the best viewing method for your terminal
- Displays images with optimal sizing based on image dimensions and terminal size
- Shows the image location without verbose technical details

### Recommended Dependencies

- **chafa 1.12.0+**: For best terminal image viewing quality, automatically installed when needed
  - Ubuntu/Debian:
    - Ubuntu 22.04 and earlier: `sudo add-apt-repository ppa:hpjansson/chafa && sudo apt-get update && sudo apt-get install chafa`
    - Ubuntu 24.04 (Noble) and later: `sudo apt install chafa` (then compile from source for best results - see below)
  - macOS: `brew install chafa`
  - Fedora/RHEL: `sudo dnf copr enable hpjansson/chafa && sudo dnf install chafa`
  - Arch Linux: `sudo pacman -S chafa`
  - **Compile from source** (recommended for latest version with all features):
    ```bash
    # Install dependencies
    sudo apt install -y build-essential automake libtool pkg-config libglib2.0-dev libmagickwand-dev libwebp-dev libavcodec-dev
    
    # Clone and build
    git clone https://github.com/hpjansson/chafa.git
    cd chafa
    ./autogen.sh
    make
    sudo make install
    ```

For automatic installation of all image viewing dependencies:
```bash
./install_image_deps.sh
```

### Version Note
- Using chafa version 1.12.0 or higher is **highly recommended** for proper image display
- Older versions may display square images incorrectly (appearing stretched or split)
- The latest version supports the `--pixel-aspect` option for proper aspect ratio adjustment
- Ubuntu 24.04 (Noble) and newer versions may not support the PPA, so compiling from source is recommended

## Usage

### Configuration

Before using CLIche, set up your provider and API key:

1. Set up your API keys:
```bash
# Set up OpenAI
cliche config --provider openai --api-key your_key_here

# Or Anthropic
cliche config --provider anthropic --api-key your_key_here

# Or Google
cliche config --provider google --api-key your_key_here

# Or DeepSeek
cliche config --provider deepseek --api-key your_key_here

# Or OpenRouter
cliche config --provider openrouter --api-key your_key_here

# Or Ollama
cliche config --provider ollama --model llama3.2:8b

# Set up Unsplash (for images)
cliche config --unsplash-key your_unsplash_api_key
```

2. Ask a question:
```bash
cliche ask "What is the meaning of life?"
```

3. Generate some code:
```bash
cliche code "make me a snake game" --lang python
```

4. Research a topic online:
```bash
cliche research "Latest developments in AI regulation" - get a response in your terminal
cliche research "Latest developments in AI regulation" --write --format markdown - write a markdown document
cliche research "Mars exploration" --write --image "mars rover" --image-count 2 - write a document with images
```

5. Scrape a website for information:
```bash
cliche scrape "https://docs.python.org/3/" --topic "Python async" --depth 2
```

6. Generate a document from scraped content:
```bash
cliche generate "Python async" --format markdown
cliche generate "Python async" --format markdown --image "python code" --image-count 3
```

7. Get system information:
```bash
cliche system
```

8. List running servers:
```bash
cliche servers
```

9. Get roasted:
```bash
cliche roastme
```

10. Generate ASCII/ANSI art with the unified command:
```bash
cliche create --ascii "Hello World"  # Generate ASCII text art
cliche create --ansi                 # Show random ANSI art
cliche create --banner "My Project"  # Generate a banner-style header
cliche create --list-fonts           # List available fonts
cliche create "Cool Text"            # Default to ASCII art with text
```

11. Generate AI images with DALL-E or Stability AI:
```bash
# Generate an image with DALL-E (default)
cliche image "a colorful landscape with mountains and a lake" --generate
```

Generated images are automatically displayed in your terminal with a clean, minimal interface. You'll see the file location and have options to view it again or open it with your system viewer.

12. View a generated file:
```bash
cliche view my_file.md --format write
cliche view game.py --format code
cliche view research_commands_in_linux.md --format docs --source research
cliche view python_async_markdown.md --format docs --source scrape
# Or simply by filename, which will search in all docs directories:
cliche view research_commands_in_linux.md
```

13. Search for files:
```bash
cliche search -t py    # Find all Python files in your home directory
cliche search -n "*.md" -l  # Find markdown files in current directory
```

14. Draw ASCII or ANSI art:
```bash
cliche draw                      # Start the drawing editor
cliche draw --ascii              # Start in ASCII mode
cliche draw --ansi               # Start in ANSI mode
cliche draw -w 100 -h 40         # Set custom canvas size
cliche draw -o myart.dur         # Specify output file
```

15. Work with images:
```bash
cliche image "mountain landscape" --list  # Search for images
cliche image --download abcd1234  # Download a specific image
cliche write "A travel guide to Japan" --format markdown --image "japan travel" --image-count 3  # Create document with images
```

## Web Research

The `research` command allows you to get up-to-date information from the web:

```bash
# Basic research
cliche research "Current state of quantum computing"

# Research with more sources
cliche research "History of artificial intelligence" --depth 5

# Generate a markdown document
cliche research "Space exploration milestones" --write --format markdown

# Generate a document with images
cliche research "Marine biology" --write --format markdown --image "ocean life" --image-count 4

# Generate a concise summary document
cliche research "Artificial intelligence trends" --write --summarize

# Generate a very brief snippet (2-3 paragraphs)
cliche research "Climate change effects" --snippet
```

The `research` command offers three different document modes:
- **Comprehensive** (default): Detailed, in-depth documents with full technical detail
- **Summary** (`--summarize`): More concise documents focusing on key information (~800-1000 words)
- **Snippet** (`--snippet`): Very brief overviews for quick consumption (2-3 paragraphs)

See [RESEARCH_COMMAND_README.md](RESEARCH_COMMAND_README.md) for more details.

## Web Scraping & Document Generation

The `scrape` and `generate` commands work together to extract and process web content:

```bash
# Scrape a specific URL with topic focus
cliche scrape "https://docs.python.org/3/library/asyncio.html" --topic "Python async"

# Generate a comprehensive document from previously scraped content (default)
cliche generate "Python async" --format markdown

# Generate a concise summary document instead
cliche generate "Python async" --format markdown --summarize

# Generate a document with images
cliche generate "Python async" --format markdown --image "python programming" --image-count 2
```

The `generate`

## Configuration Management

CLIche offers two ways to manage your configuration:

1. Using the `config` command for API keys and model settings:
```bash
cliche config --provider openai --api-key your_api_key_here
cliche config --provider openai --model gpt-4
cliche config --provider anthropic --api-key your_anthropic_key
```

2. Using the `config-manager` command for more advanced configuration:
```bash
# Using subcommands (traditional approach)
cliche config-manager show           # Show current configuration
cliche config-manager backup         # Create a backup of config
cliche config-manager create         # Create a default config if none exists
cliche config-manager reset          # Reset to default config
cliche config-manager edit           # Open config in editor

# Using direct flags (convenient shortcuts)
cliche config-manager --show         # Show current configuration
cliche config-manager --backup       # Create a backup of config
cliche config-manager --create       # Create a default config if none exists
cliche config-manager --reset        # Reset to default config
cliche config-manager --edit         # Open config in editor
```

Both `config` and `config-manager` commands store settings in `~/.config/cliche/config.json`.

## Command Usage Flexibility

CLIche offers a flexible dual command pattern that lets you use commands in two ways:

### 1. Flag Style (with double-dash)

```bash
cliche config-manager --show
cliche config-manager --backup
cliche research --web "machine learning"
```

### 2. Subcommand Style (without double-dash)

```bash
cliche config-manager show
cliche config-manager backup
cliche research web "machine learning"
```

Both styles work interchangeably for supported commands, letting you use whichever approach you prefer. This flexibility makes CLIche more intuitive regardless of your command-line habits.

## Scrape Command

The `scrape` command extracts structured content from websites, with enhanced link-following capabilities:

```bash
# Basic scraping of a single URL
cliche scrape https://docs.github.com

# Advanced scraping with depth and page limits
cliche scrape https://example.com --depth 3 --max-pages 5 --debug

# Generate a markdown document from scraped content
cliche scrape https://docs.python.org --write --format markdown

# Add images to generated document
cliche scrape https://flask.palletsprojects.com --write --image "flask web" --image-count 2
```

**Key Parameters:**
- `--depth`: Controls how many levels of links to follow (1 = just the URL, 2+ = follow links)
- `--max-pages`: Limits the total number of pages crawled across all depth levels
- `--debug`: Shows detailed information about the crawling process and content extraction
- `--write`: Generates a document from the scraped content
