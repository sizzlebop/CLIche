# CLIche
### A snarky, all-knowing LLM terminal assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

Turn your terminal into a wise-cracking genius with a snarky, all-knowing LLM assistant.

## Features

- 🧠 Multiple LLM providers support:
  - OpenAI (GPT-4o, O3-mini)
  - Anthropic (Claude)
  - Google (Gemini)
  - DeepSeek
  - OpenRouter
  - Ollama (Local models)
- 🎨 Generate random ANSI art
- 🔥 Get roasted about your programming habits
- 💻 View system information
- 🔌 List and manage running servers
- ⚙️ Easy configuration for API keys and model settings
- 😏 Snarky responses included at no extra charge

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

## Configuration

Configure your preferred LLM provider:

```bash
# Use OpenAI
cliche config --provider openai --api-key your-api-key-here

# Use Anthropic
cliche config --provider anthropic --api-key your-api-key-here

# Use local models with Ollama
cliche config --provider ollama --model codellama  # or any other model
```

Configuration is stored in `~/.config/cliche/config.json`.

## Usage

### Ask Questions
```bash
cliche ask "How do I reverse a linked list in Python?"
cliche ask "What's the meaning of life?"
```

### Generate ANSI Art
```bash
cliche ansi
```

### Get Roasted
```bash
cliche roastme
```

### System Information
```bash
cliche sysinfo
```

### Server Management
```bash
# List running servers
cliche servers

# Kill a process
cliche kill 1234  # Replace with actual PID
```

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

## Contributing

Found a bug? Have a feature idea? Want to make it even snarkier? Pull requests welcome!

## License

MIT License - Feel free to use it, just don't blame me for any hurt feelings from the roasts.