# Changelog

All notable changes to CLIche will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 🔍 Improved server detection in `servers` command:
  - Now detects all processes listening on localhost ports
  - Added detection for AI/ML servers (Ollama, TensorBoard, MLflow, etc.)
  - Added detection for development servers and generic servers
  - Shows ports even for unknown servers
  - Filters out system processes and IDE-related services
  - Better categorization of unknown servers
  - Improved sorting by server type
- 🔎 Enhanced `find` command:
  - Now uses `fd` for faster and more powerful searching
  - Added support for hidden files, case sensitivity, max depth
  - Added exclude patterns support
  - Better output formatting with icons
  - Added helpful examples in docstring
  - Added installation instructions if `fd` is not found
- 🎨 Improved write command output:
  - Shows LLM's explanation/commentary in terminal
  - Only saves code to file when generating code
  - Added progress indicators for better UX
  - Fixed code block extraction for more reliable results
- ✨ Enhanced `write` command with multi-language support:
  - Added support for Python, JavaScript, TypeScript, Ruby, Rust, Go, C++, C#, Java, PHP, Swift, Kotlin
  - Added language aliases (py -> python, rs -> rust, etc.)
  - Intelligent file extension mapping
  - Language-specific code generation with proper structure
  - Special handling for JavaScript animations with HTML
  - Improved code block detection and cleanup
- ✨ Providers: Added DeepSeek provider support
- ✨ Providers: Added OpenRouter provider support
- 🔍 Models: Enhanced models command to list available models for all providers

### Changed
- 🔧 Providers: Made system info optional in context with new `include_sys_info` parameter
- 🎯 Roast: Removed tech-themed roasts and system info from regular roasts
- 🔄 Roast: Increased max tokens to 300 to prevent truncated responses
- 📝 Models: Updated model lists with latest versions for all providers
  - OpenAI: Added O-series models (4O, O3, O1)
  - Anthropic: Updated to Claude 3.5 models (Sonnet, Haiku, Opus)
  - Google: Updated to Gemini 1.5 models with version aliases
  - DeepSeek: Added extended context models
  - OpenRouter: Improved model filtering and sorting

## [0.1.0] - 2025-02-23

### Added
- 🎯 Initial release of CLIche
- ✨ Core functionality for interacting with various LLM providers
- 🔧 Configuration management system
- 🤖 Support for OpenAI, Anthropic, Google, and Ollama providers
- 🛠️ Basic CLI commands:
  - `config`: Configure provider settings
  - `models`: List available Ollama models
  - `servers`: List running servers
  - `kill`: Kill processes

### Changed
- 🏗️ Reorganized project structure:
  - Moved Config class to core.py
  - Separated provider implementations into individual modules
  - Created utils directory for shared functionality
  - Centralized CLI commands in commands directory
- 🔄 Simplified configuration options:
  - Removed host and personality options from config command
  - Streamlined provider configuration process

### Fixed
- 🐛 Fixed circular import issues between modules
- 🔍 Improved GPU detection reliability
- 🔐 Better handling of API keys and provider settings

### Technical
- 📦 Modular architecture with clear separation of concerns
- 🔌 Extensible provider system for easy addition of new LLM services
- 🧪 Base provider class with common functionality
- 📊 System information gathering for context-aware responses
