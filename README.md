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

### Enhanced Web Scraping & Research

- **Deep Content Extraction**: Extract up to 1 million characters from websites with the `scrape` command
- **Improved Research**: Get up to 100,000 characters per page with the `research` command
- **Browser-Based Rendering**: Better support for JavaScript-heavy websites
- **Specialized Extractors**: Optimized extraction for Wikipedia and Python documentation

```bash
# Scrape a website deeply
cliche scrape https://docs.python.org/3/library/asyncio.html --depth 3 --max-pages 10

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

Choose one of these methods:

### Method 1: Automatic Installation Script (Recommended)

```bash
# Clone the repository
git clone https://github.com/sizzlebop/cliche.git
cd cliche

# Run the installation script
./install.sh
```

### Method 2: Manual Installation

```bash
# Clone the repository
git clone https://github.com/sizzlebop/cliche.git
cd cliche

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .
```

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

10. Get a random ASCII art pattern:
```bash
cliche art
cliche art "hello" - get a specific ASCII art pattern
```

11. Get a random ANSi art pattern:
```bash
cliche ansi
```

12. Create ASCII/ANSI art with the new unified command:
```bash
cliche create --ascii "Hello World"  # Create ASCII text art
cliche create --ansi                 # Show random ANSI art  
cliche create --banner "My Project"  # Create a banner-style header
cliche create --list-fonts           # List available fonts
cliche create "Cool Text"            # Default to ASCII art with text
```

13. Generate AI images with DALL-E or Stability AI:
```bash
# Generate an image with DALL-E (default)
cliche image "a colorful landscape with mountains and a lake" --generate

# Specify a provider and model
cliche image "a medieval castle on a hill at sunset" --generate --provider dalle --model dall-e-2

# Customize style and size
cliche image "a futuristic cityscape with flying cars" --generate --style natural --size 1024x1024

# List available providers, models, and styles
cliche image --list-providers
cliche image --list-models dalle
cliche image --list-styles dalle
```

Generated images are automatically displayed in your terminal with a clean, minimal interface. You'll see the file location and have options to view it again or open it with your system viewer.

14. View a generated file:
```bash
cliche view my_file.md --format write
cliche view game.py --format code
cliche view research_commands_in_linux.md --format docs --source research
cliche view python_async_markdown.md --format docs --source scrape
# Or simply by filename, which will search in all docs directories:
cliche view research_commands_in_linux.md
```

15. Search for files:
```bash
cliche search -t py    # Find all Python files in your home directory
cliche search -n "*.md" -l  # Find markdown files in current directory
```

16. Work with images:
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