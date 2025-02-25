# CLIche

🤖 A command-line interface for interacting with various LLM providers with a snarky personality.

### A snarky, all-knowing LLM terminal assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

Turn your terminal into a wise-cracking genius with a snarky, all-knowing LLM assistant. Plus, gain the power to research topics, scrape websites, and generate professional documents.

## Latest Features

- 🔍 **Web Research**: Get up-to-date information from the web with `research` command
- 🕸️ **Web Scraping**: Extract and save content from websites with `scrape` command
- 📝 **Document Generation**: Create professional documents from scraped data
- 🎭 **Personality Switching**: Toggle between snarky and professional tones

## Core Features

- 🔄 **Multi-provider support**:
  - OpenAI (GPT-4, GPT-3.5, O-series)
  - Anthropic (Claude 3.5)
  - Google (Gemini 2.0)
  - DeepSeek (Chat, Coder)
  - OpenRouter (Free models)
  - Ollama (Local models)
- 🎯 Easy provider switching
- 🔐 Secure API key management
- ✨ **Generation commands**:
  - `code`: Generate code in any language
  - `write`: Generate text, markdown, or HTML content
  - `research`: Search the web and generate responses based on current information
  - `scrape`: Extract and save web content
  - `generate`: Create documents from scraped content
- 🎨 **Art & ANSI support**:
  - Generate ASCII text art with custom fonts
  - Display random ASCII art patterns
  - Show custom ANSI art collection
- 🛠️ GPU and Docker utilities
- 📝 Rich configuration options
- 🔥 Get roasted about your programming habits
- 💻 View system information
- 🔌 List and manage running servers
- 😏 Snarky responses included at no extra charge

## Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/sizzlebop/cliche.git
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
export OPENAI_API_KEY=your_key_here

# Or Anthropic
export ANTHROPIC_API_KEY=your_key_here

# Or Google
export GOOGLE_API_KEY=your_key_here
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
cliche research "Latest developments in AI regulation"
```

5. Scrape a website for information:
```bash
cliche scrape "https://docs.python.org/3/" --topic "Python async" --depth 2
```

6. Generate a document from scraped content:
```bash
cliche generate "Python async" --format markdown
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
```

See [RESEARCH_COMMAND_README.md](RESEARCH_COMMAND_README.md) for more details.

## Web Scraping & Document Generation

The `scrape` and `generate` commands work together to extract and process web content:

```bash
# Scrape a specific URL with topic focus
cliche scrape "https://docs.python.org/3/library/asyncio.html" --topic "Python async"

# Generate a document from previously scraped content
cliche generate "Python async" --format markdown
```

See [SCRAPE_COMMAND_README.md](SCRAPE_COMMAND_README.md) for more details.

## Helper Scripts

CLIche includes several helper scripts for common operations:

- `scrape.sh`: Helper for topic-based scraping
- `generate.sh`: Helper for document generation
- `cliche-bypass`: Run CLIche in an isolated environment

Example usage:
```bash
./scrape.sh "https://docs.github.com" "GitHub Copilot" 2 5
./generate.sh "GitHub Copilot" markdown
```

## Configuration

Configure your preferred providers and settings with the `config` command:

```bash
# Configure OpenAI provider
cliche config --provider openai --api-key your_api_key

# Configure Ollama provider
cliche config --provider ollama --model llama3
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
3. Set it up with: `cliche config --provider ollama --model llama3`

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions, please:
1. Check the [FAQ](docs/FAQ.md)
2. Search existing [Issues](https://github.com/sizzlebop/cliche/issues)
3. Create a new issue if needed

---
Made with ❤️ by Pink Pixel
Dream it, Pixel it ✨