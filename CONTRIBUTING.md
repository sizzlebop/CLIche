# Contributing to CLIche

Thank you for considering contributing to CLIche! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
   ```bash
   git clone https://github.com/YOUR-USERNAME/cliche.git
   cd cliche
   ```
3. **Set up your development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .
   ```
4. **Create a new branch** for your feature or bugfix
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

### Testing

- Write tests for new features and bug fixes
- Ensure all tests pass before submitting a pull request
- Run tests with `pytest`

### Documentation

- Update the README.md if you change functionality
- Add new commands to the command reference
- Update the CHANGELOG.md for significant changes
- Document complex functions with detailed docstrings

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

4. **Address review comments** if requested by maintainers

## Feature Requests and Bug Reports

- Use the GitHub issue tracker to submit bug reports and feature requests
- Provide detailed information about bugs, including steps to reproduce
- For feature requests, explain the use case and benefits

## Adding New Providers

When adding a new LLM provider:

1. Create a new provider file in the `providers` directory
2. Implement the required provider interface
3. Add configuration options to the config system
4. Update documentation and help text
5. Add tests for the new provider

## License

By contributing to CLIche, you agree that your contributions will be licensed under the project's MIT License.

---

Thank you for contributing to CLIche! Your help makes this project better for everyone.

Made with ❤️ by Pink Pixel
Dream it, Pixel it ✨ 