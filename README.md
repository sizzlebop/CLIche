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
- 🎨 Art & ANSI support:
  - Generate ASCII text art with custom fonts
  - Display random ASCII art patterns
  - Show custom ANSI art collection
- 🛠️ GPU and Docker utilities
- 📝 Rich configuration options
- 🧠 Multiple LLM providers support:
  - OpenAI (GPT-4o, O3-mini)
  - Anthropic (Claude)
  - Google (Gemini)
  - DeepSeek
  - OpenRouter
  - Ollama (Local models)
- 🎨 Art commands:
  - Generate ASCII text art with custom fonts
  - Display random ASCII art patterns
  - Show custom ANSI art collection
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

## Configuration

1. Copy the template environment file:
```bash
cp .env.template ~/.config/cliche/.env
```

2. Edit the `.env` file with your API keys:
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
GOOGLE_API_KEY=...
DEEPSEEK_API_KEY=...
OPENROUTER_API_KEY=...
```

3. Configure your preferred provider:
```bash
cliche config provider openai
cliche config model gpt-4
```

## Usage

```bash
# Chat with your AI assistant
cliche ask "What's the meaning of life?"

# Configure your provider
cliche config provider openai
cliche config key YOUR_API_KEY

# List available models
cliche models

# Generate ASCII art
cliche art "Hello"  # Create text art
cliche art --font block "Cool"  # Use specific font
cliche art --random  # Show random art pattern

# Display ANSI art
cliche ansi  # Show random art from collection
cliche ansi --index 0  # Show specific art piece

# Get roasted
cliche roastme

# View system info
cliche system

# List running servers
cliche servers

# Kill a process
cliche kill PID
```

## Development

```bash
# Create conda environment
conda env create -f environment.yml

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black cliche/
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m '✨ feat: Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to all the LLM providers for their amazing APIs
- Special thanks to the open-source community

Made with ❤️ by Pink Pixel

## Quick Install

```bash
# Clone the repository
git clone https://github.com/pinkpixel-dev/cliche.git
cd cliche

# Run the install script
chmod +x install.sh
./install.sh

# Load the alias
source ~/.bashrc
```

## Environment Variables

You can store your API keys in a `.env` file located at `~/.config/cliche/.env`. This allows you to easily switch between different providers without having to reconfigure API keys each time.

Copy the `.env.template` file to `~/.config/cliche/.env` and fill in your API keys:

```bash
mkdir -p ~/.config/cliche
cp .env.template ~/.config/cliche/.env
```

Then edit the `.env` file with your API keys:

```env
# API Keys for different providers
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here
OPENROUTER_API_KEY=your_openrouter_key_here

# Optional configurations
OLLAMA_HOST=http://localhost:11434
```

Once configured, you can easily switch between providers and models:

```bash
cliche config --provider openai --model gpt-4o
cliche config --provider anthropic --model claude-3.5-sonnet-20240307
```

The API keys will be automatically loaded from your `.env` file.

## LLM Provider Setup

### Using Local Models with Ollama

1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Start the Ollama service:
```bash
ollama serve
```
3. Pull your desired model:
```bash
# Pull the base Llama2 model
ollama pull llama2

# Or pull CodeLlama for programming tasks
ollama pull codellama

# Or pull Mistral
ollama pull mistral
```
4. Configure CLIche to use Ollama:
```bash
# Switch to Ollama provider with your chosen model
cliche config --provider ollama --model llama2

# List available models
cliche models
```

Ollama runs locally on your machine, so no API keys are needed!

### OpenAI
1. Get API key from [OpenAI Platform](https://platform.openai.com/)
2. Run: `cliche config --provider openai --api-key your-key`

### Anthropic
1. Get API key from [Anthropic Console](https://console.anthropic.com/)
2. Run: `cliche config --provider anthropic --api-key your-key`

### Google AI
1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Run: `cliche config --provider google --api-key your-key`

### DeepSeek
1. Get API key from [DeepSeek Platform](https://platform.deepseek.com/)
2. Run: `cliche config --provider deepseek --api-key your-key`

### OpenRouter
1. Get API key from [OpenRouter](https://openrouter.ai/)
2. Run: `cliche config --provider openrouter --api-key your-key`

## Requirements

- Python 3.7+
- For cloud providers: API keys
- For local models: Ollama installed
- Sense of humor (optional but recommended)

## Troubleshooting

1. **Command not found**: 
   - Run `source ~/.bashrc` or start a new terminal session
   - Verify installation path is in your PATH variable
   - Check if install.sh completed successfully

2. **API errors**: 
   - Verify your API keys in `~/.config/cliche/config.json`
   - Check API key permissions and quotas
   - Ensure network connectivity

3. **Provider unavailable**: 
   - Make sure you've configured an API key for your chosen provider
   - Check provider status page for outages
   - Verify network connectivity

4. **Ollama not responding**: 
   - Run `ollama serve` in a separate terminal
   - Check if Ollama is properly installed
   - Verify system resources (RAM/CPU)
   - Check Ollama logs: `journalctl -u ollama`

5. **Model not found**: 
   - Run `ollama pull model-name` to download the model first
   - Check available disk space
   - Verify model compatibility with your system

6. **Performance issues**:
   - Check system resources usage
   - Consider using a lighter model
   - Clear model cache if using Ollama

For more detailed troubleshooting, visit our [Wiki](https://github.com/yourusername/cliche/wiki).