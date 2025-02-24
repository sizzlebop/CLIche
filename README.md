# CLIche

🤖 A command-line interface for interacting with various LLM providers.

### A snarky, all-knowing LLM terminal assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

Turn your terminal into a wise-cracking genius with a snarky, all-knowing LLM assistant.

## Features

- 🔄 Multi-provider support:
  - OpenAI (GPT-4, GPT-3.5, O-series)
  - Anthropic (Claude 3.5)
  - Google (Gemini 1.5)
  - DeepSeek (Chat, Coder, Math)
  - OpenRouter (Free models)
  - Ollama (Local models)
- 🎯 Easy provider switching
- 🔐 Secure API key management
- ✨ Generation commands:
  - `code`: Generate code in any language
  - `write`: Generate text, markdown, or HTML content
  - `view`: View generated files with proper formatting
  - `scrape`: Extract and save web content ([docs/web_scraping.md](docs/web_scraping.md))
- 🎨 Art & ANSI support:
  - Generate ASCII text art with custom fonts
  - Display random ASCII art patterns
  - Show custom ANSI art collection
- 🛠️ GPU and Docker utilities
- 📝 Rich configuration options
- 🔥 Get roasted about your programming habits
- 💻 View system information
- 🔌 List and manage running servers
- ⚙️ Easy configuration for API keys and model settings
- 😏 Snarky responses included at no extra charge

## Installation

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install from PyPI
pip install cliche-cli

# Or install from source
git clone https://github.com/sizzlebop/cliche.git
cd cliche
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

2. Generate some code:
```bash
# Generate a Python game
cliche code make me a snake game --lang python

# Generate a React component
cliche code create a login form --lang javascript
```

3. Write some content:
```bash
# Generate a markdown tutorial
cliche write a tutorial on docker --type markdown

# Generate an HTML blog post
cliche write a blog post about AI --type html
```

4. View generated files:
```bash
# View a markdown file
cliche view tutorial.md

# View generated code
cliche view game.py --type code
```

## File Organization

Generated files are stored in:
- Code: `~/.cliche/files/code/`
- Text: `~/.cliche/files/write/`

## Configuration

Configure your preferred providers and settings in `~/.cliche/config.yaml`:

```yaml
default_provider: openai
default_model: gpt-4
include_sys_info: true
```

## Providers

### OpenAI
1. Get your API key from [OpenAI](https://platform.openai.com)
2. Set the environment variable:
```bash
export OPENAI_API_KEY=your_key_here
```

### Anthropic
1. Get your API key from [Anthropic](https://console.anthropic.com)
2. Set the environment variable:
```bash
export ANTHROPIC_API_KEY=your_key_here
```

### Google
1. Get your API key from [Google AI Studio](https://makersuite.google.com)
2. Set the environment variable:
```bash
export GOOGLE_API_KEY=your_key_here
```

### DeepSeek
1. Get your API key from [DeepSeek](https://platform.deepseek.ai)
2. Set the environment variable:
```bash
export DEEPSEEK_API_KEY=your_key_here
```

### OpenRouter
1. Get your API key from [OpenRouter](https://openrouter.ai)
2. Set the environment variable:
```bash
export OPENROUTER_API_KEY=your_key_here
```

### Ollama (Local Models)
1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Start the Ollama service:
```bash
ollama serve
```

## Web Scraping

The `scrape` command allows you to extract content from websites and save it as markdown:

```bash
# Basic scraping
cliche scrape "https://example.com"

# Focused scraping on a specific topic
cliche scrape "https://example.com" --topic "Python Variables"
```

Features:
- Follows links within the same domain (up to 100 pages)
- Filters out navigation and tool links
- Optional topic filtering to focus on relevant content
- Saves output as clean markdown files

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to all the LLM providers for their amazing models
- Special thanks to our contributors and users

## Support

If you encounter any issues or have questions, please:
1. Check the [FAQ](docs/FAQ.md)
2. Search existing [Issues](https://github.com/sizzlebop/cliche/issues)
3. Create a new issue if needed

---
Made with ❤️ by Pink Pixel