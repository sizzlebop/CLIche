# Contributing to CLIche

Thank you for considering contributing to CLIche! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Development Guidelines](#development-guidelines)
- [Adding New Commands](#adding-new-commands)
- [Adding New Providers](#adding-new-providers)
- [Testing Framework](#testing-framework)
- [Documentation Standards](#documentation-standards)
- [Pull Request Process](#pull-request-process)
- [Feature Requests and Bug Reports](#feature-requests-and-bug-reports)
- [Release Process](#release-process)
- [License](#license)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## Project Structure

CLIche is organized as follows:

```
cliche/
├── commands/      # Command implementations
├── providers/     # LLM provider integrations
├── utils/         # Utility functions and helpers
├── core.py        # Core CLI functionality
├── prompts.py     # LLM prompts
├── __init__.py    # Package initialization and command registration
├── __main__.py    # Entry point
docs/              # Documentation files
tests/             # Test suite
```

Key components:
- **commands/**: Each file implements a specific CLI command
- **providers/**: Provider-specific implementations for different LLM services
- **utils/**: Helper functions for file operations, configuration, and content processing
- **core.py**: Main CLI application and configuration handling

## Getting Started

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
   ```bash
   git clone https://github.com/YOUR-USERNAME/cliche.git
   cd cliche
   ```

### Development Environment Setup

#### Option 1: Using the Installation Script (Recommended)
```bash
# Run the installation script for a complete setup
./install.sh
```

#### Option 2: Manual Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### API Keys for Testing

Create a `.env` file in the root directory with your API keys:
```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
UNSPLASH_API_KEY=your_unsplash_key
STABILITY_API_KEY=your_stability_key
BRAVE_API_KEY=your_brave_key
```

### Branch Creation
Create a new branch for your feature or bugfix:
```bash
git checkout -b feature/your-feature-name
```

## Development Guidelines

### Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code
- Use meaningful variable and function names
- Include docstrings for all functions, classes, and modules
- Add type hints wherever possible
- Use comments to explain complex logic
- Use 4 spaces for indentation (not tabs)

### Best Practices

- Keep functions focused on a single responsibility
- Limit function length to improve readability
- Use consistent naming conventions throughout the codebase
- Handle errors gracefully with helpful error messages
- Make user-facing text clear and consistent in tone
- Follow the existing patterns for command implementation

## Adding New Commands

New commands should be added as separate files in the `cliche/commands/` directory, following these steps:

1. Create a new file in the `cliche/commands/` directory (e.g., `your_command.py`)
2. Implement your command using Click decorators
3. Register your command in `cliche/__init__.py`

### Command Template

```python
"""
Brief description of what the command does.
"""
import click
from ..core import cli, get_llm  # Import common utilities as needed
from ..utils.file import save_text_to_file  # Import specific utilities

@cli.command()
@click.argument('argument', required=True)
@click.option('--option', help='Description of option')
@click.option('--flag', is_flag=True, help='Description of flag')
def your_command(argument, option, flag):
    """Command help text that appears in --help.
    
    Detailed description of command functionality.
    
    Examples:
        cliche your-command "example input"
        cliche your-command "another example" --option value
    """
    # Command implementation
    # ...
```

### Command Registration

Add your command to `cliche/__init__.py`:

```python
from .commands.your_command import your_command

# ... other imports ...

cli.add_command(your_command)
```

## Adding New Providers

When adding a new LLM provider:

1. Create a new provider file in the `providers` directory (e.g., `newprovider.py`)
2. Implement the provider class following the base provider pattern
3. Add configuration options to the config system
4. Update the provider factory in `providers/__init__.py`
5. Add tests for the new provider

### Provider Template

```python
"""
Integration with NewProvider LLM service.
"""
from typing import Dict, Any, Optional
from .base import ProviderBase

class NewProviderProvider(ProviderBase):
    """Implementation for the NewProvider LLM service."""
    
    def __init__(self, api_key: str, model: str):
        """Initialize the provider with API key and model."""
        self.api_key = api_key
        self.model = model
        # Any other initialization
        
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response from the NewProvider API."""
        # Implementation details
        # Return the generated text
```

## Testing Framework

### Test Structure

CLIche's tests are organized as follows:
- `tests/unit/`: Unit tests for individual components
- `tests/integration/`: Tests for component interactions
- `tests/commands/`: Tests for CLI commands
- `tests/providers/`: Tests for LLM providers

### Running Tests

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/

# Run with coverage report
pytest --cov=cliche

# Run specific test file
pytest tests/unit/test_specific_file.py
```

### Test Requirements

- All new features must include unit tests
- Command tests should verify both successful execution and error handling
- Aim for at least 80% test coverage for new code
- Include tests for edge cases and invalid inputs
- Mock external services where appropriate

### Example Test

```python
import pytest
from click.testing import CliRunner
from cliche.commands.your_command import your_command

def test_your_command_basic():
    """Test basic functionality of your_command."""
    runner = CliRunner()
    result = runner.invoke(your_command, ["test argument"])
    assert result.exit_code == 0
    assert "Expected output" in result.output
```

## Documentation Standards

### Command Help Text

- Begin with a short, single-line description
- Follow with a more detailed explanation
- Include 2-3 example usages
- Document all options and arguments

### README Updates

When adding a new command, update:
1. The features list if applicable
2. The command reference section
3. Add an example usage in the examples section

### CHANGELOG Format

Use emoji prefixes for different change types:
- ✨ New feature
- 🔧 Enhancement
- 🐛 Bug fix
- 📝 Documentation
- 🧪 Testing
- 🚀 Performance
- 🔒 Security

Example:
```
### Added
- ✨ New `your-command` for processing data
  - Feature detail 1
  - Feature detail 2
```

### Documenting New Commands

For significant new commands, consider creating a dedicated documentation file in the `docs/` directory, following the pattern of existing command documentation.

## Pull Request Process

1. **Update your fork** with the latest changes from the main repository
   ```bash
   git remote add upstream https://github.com/sizzlebop/cliche.git
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push your changes** to your fork
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Submit a pull request** from your fork to the main repository
   - Provide a clear description of the changes
   - Reference any related issues
   - Explain the impact of your changes
   - Include screenshots for UI changes (if applicable)
   - Verify that tests pass

4. **Address review comments** if requested by maintainers

5. **Update your PR** if necessary by pushing additional commits to your branch

## Feature Requests and Bug Reports

- Use the GitHub issue tracker to submit bug reports and feature requests
- Provide detailed information about bugs, including steps to reproduce
- For feature requests, explain the use case and benefits
- Use the issue templates when available
- Check existing issues before creating new ones to avoid duplicates

### Bug Report Format

When reporting bugs, include:
- CLIche version
- Operating system and Python version
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages and stack traces (if applicable)
- Any relevant configuration

## Release Process

CLIche follows [Semantic Versioning](https://semver.org/):
- MAJOR version for incompatible API changes
- MINOR version for backwards-compatible functionality
- PATCH version for backwards-compatible bug fixes

### Release Checklist

1. Update version in `cliche/__init__.py`
2. Update CHANGELOG.md with the new version and date
3. Create a new GitHub release with release notes
4. Update documentation to reflect new features
5. Verify all tests pass on the release branch

### Versioning

Version format: `MAJOR.MINOR.PATCH`

Example versions:
- `1.0.0` - Initial stable release
- `1.1.0` - New feature added
- `1.1.1` - Bug fix

## License

By contributing to CLIche, you agree that your contributions will be licensed under the project's MIT License.

---

Thank you for contributing to CLIche! Your help makes this project better for everyone.

Made with ❤️ by Pink Pixel
Dream it, Pixel it ✨ 