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
- 🖼️ **Image Integration**: Beautiful images from Unsplash with direct URLs for better sharing and compatibility
- 🎨 **Art & ANSI support**:
  - Generate ASCII text art with custom fonts
  - Display random ASCII art patterns
  - Display random ANSI art patterns


- ✨ **Base commands**:
  - `ask`: Ask the AI a question
  - `roastme`: Get roasted by the AI
  - `art`: Display random ASCII art patterns
  - `ansi`: Display random ANSI art patterns
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

### Quick Install

```bash
# Clone the repository
git clone https://github.com/pinkpixel-dev/cliche.git
cd cliche

# Run the installation script
./install.sh
```

### Manual Installation

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

## Quick Start

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

14. Work with images:
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

The `generate` command uses an advanced chunking approach that:
- Extracts major sections from scraped content
- Processes each section individually with the LLM
- Preserves all technical details and code examples
- Handles large content volumes efficiently

See [SCRAPE_COMMAND_README.md](SCRAPE_COMMAND_README.md) for more details.

## Image Integration with Direct URLs

When using the `--image` option with commands like `research`, `generate`, or `write`, CLIche embeds images with direct URLs from Unsplash instead of downloading them locally. This offers several advantages:

1. **Better compatibility** - Works with all markdown viewers and platforms
2. **Improved sharing** - Documents can be shared without needing to include image files
3. **Standard compliance** - Uses standard markdown image syntax

### AI-Powered Image Placement

CLIche uses advanced AI to intelligently place images at contextually relevant positions in your documents:

1. **Content Analysis** - The AI analyzes your document content to understand the topics and concepts
2. **Optimal Positioning** - Images are placed at locations where they best enhance understanding
3. **Natural Integration** - No more arbitrary image placement or manual placeholders required
4. **Consistent Experience** - The same powerful approach is used across all document generation commands

When no explicit image placeholders are found, the system automatically:
- Analyzes document content and structure
- Identifies key sections and concepts
- Places images at points that complement the surrounding text
- Evenly distributes images if optimal positions can't be determined

Example of using AI-powered image placement:

```bash
cliche write "A guide to Mediterranean cuisine" --format markdown --image "mediterranean food" --image-count 3
```

This will create a document with three Mediterranean food images intelligently placed throughout the content at contextually relevant positions.

### Image Command for Direct Searches

The `image` command lets you search and download high-quality images from Unsplash:

```bash
# Search for images
cliche image "sunset beach" --list

# View more results with pagination
cliche image "sunset beach" --list --page 2 --count 15

# Download a specific image by ID
cliche image --download abcd1234

# Download with custom dimensions
cliche image --download abcd1234 --width 1920 --height 1080
```

You can also add images directly to generated documents:

```bash
# Add images to a write command
cliche write "A guide to sustainable living" --format markdown --image "sustainable living" --image-count 3

# Add images to research documents
cliche research "Climate change" --write --format markdown --image "climate change effects" --image-count 2

# Add images to generated documents from scraped content
cliche generate "Machine learning" --format markdown --image "ai technology" --image-count 4
```

All images in documents:
- Use direct Unsplash URLs for better compatibility and sharing
- Are automatically attributed as required by Unsplash terms
- Are properly formatted for the document type (markdown or HTML)
- Are intelligently placed using AI-powered contextual analysis

The `image` command still supports downloading images locally to `~/.cliche/files/images/` for other uses.

## Helper Scripts

CLIche includes several helper scripts for common operations:

- `scrape.sh`: Helper for topic-based scraping
- `generate.sh`: Helper for document generation
- `cliche-bypass`: Run CLIche in an isolated environment

Example usage:
```bash
./scrape.sh "https://docs.github.com" "GitHub Copilot" 2 5
./generate.sh "GitHub Copilot" markdown --image "github" --image-count 2
```

## Configuration

Configure your preferred providers and settings with the `config` command:

```bash
# Configure OpenAI provider
cliche config --provider openai --api-key your_api_key --model gpt-4o

# Configure Ollama provider
cliche config --provider ollama --model llama3.2:8b

# Configure Unsplash API for images
cliche config --unsplash-key your_unsplash_api_key
```

Your configuration is stored in `~/.config/cliche/config.json`.

## Provider Setup

### OpenAI
1. Get your API key from [OpenAI](https://platform.openai.com)
2. Set it up with: `cliche config --provider openai --api-key your_key`

### Anthropic
1. Get your API key from [Anthropic](https://console.anthropic.com)
2. Set it up with: `cliche config --provider anthropic --api-key your_key`

### Google
1. Get your API key from [Google AI Studio](https://makersuite.google.com)
2. Set it up with: `cliche config --provider google --api-key your_key`

### DeepSeek
1. Get your API key from [DeepSeek](https://platform.deepseek.ai)
2. Set it up with: `cliche config --provider deepseek --api-key your_key`

### OpenRouter
1. Get your API key from [OpenRouter](https://openrouter.ai)
2. Set it up with: `cliche config --provider openrouter --api-key your_key`

### Ollama (Local Models)
1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Start the Ollama service: `ollama serve`
3. Set it up with: `cliche config --provider ollama --model llama3.2:8b`

### Unsplash (Images)
1. Sign up at [Unsplash Developer Portal](https://unsplash.com/developers)
2. Create a new application to get your API key
3. Set it up with: `cliche config --unsplash-key your_key`

## Model configuration

You can easily switch out the model you want to use with the `config` command after your API keys are set up in the config file.
```bash
cliche config --provider openai --model gpt-4o
```

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions, please:
1. Check the [FAQ](docs/FAQ.md)
2. Search existing [Issues](https://github.com/pinkpixel-dev/cliche/issues)
3. Create a new issue if needed

## File Organization

CLIche organizes all generated files in a structured directory hierarchy:

```
~/cliche/files/
├── docs/              # All generated documents
│   ├── research/      # Research command documents
│   ├── write/         # Write command documents
│   └── scrape/        # Documents from scraped content
├── code/              # Generated code files
├── images/            # Downloaded images (when using image --download)
└── scrape/            # Raw scraped data (JSON format)
```

When multiple documents are generated with the same topic or filename, CLIche automatically adds incremental suffixes (_1, _2, etc.) to prevent overwriting existing files.

---
Made with ❤️ by Pink Pixel;
Dream it, Pixel it ✨