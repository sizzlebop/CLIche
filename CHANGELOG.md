# Changelog

All notable changes to CLIche will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- ✨ Added new `scrape` command:
  - Scrape content from any webpage
  - Save as text, markdown, or HTML
  - Smart content extraction
  - Clean output formatting
  - Automatic file naming
- ✨ Added new `view` command:
  - View generated files with proper formatting
  - Rich markdown rendering support
  - Code syntax highlighting
  - Automatic file type detection
  - Support for both code and text files
- ✨ Split write command into two separate commands:
  - `code`: Simplified code generation with `cliche code make me a game --lang python`
  - `write`: Simplified text generation with `cliche write a tutorial on docker --type markdown`
  - Both commands handle async generation and file saving
  - Improved error handling and progress indicators
  - Smart file naming and organization
- 📁 Improved file organization:
  - Code files stored in `~/.cliche/files/code/`
  - Text files stored in `~/.cliche/files/write/`
  - Automatic file extension mapping
  - Proper file permissions and encoding
- 🎨 Added rich library for terminal formatting:
  - Beautiful markdown rendering
  - Syntax highlighting for code
  - Progress indicators
  - Error messages
- ✨ Added new art commands:
  - `art`: Generate ASCII text art with custom fonts and random patterns
  - `ansi`: Display custom ANSI art collection
  - Support for random art generation and specific art selection
  - Error handling and helpful messages
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
- ✨ Added topic filtering to scrape command with `--topic` option
- 🔍 Enhanced web scraping with MediaWiki-specific link filtering
- 🎯 Improved link relevance detection for more focused content scraping

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
- 🔄 Simplified command structure:
  - Split write command into code and write commands
  - Added view command for file viewing
  - Improved help text and examples
  - Better error messages and suggestions
- 🔄 Improved file handling:
  - Better file naming strategy
  - Proper encoding and line endings
  - Removal of invisible characters
  - Smart file organization
- 🔄 Enhanced configuration:
  - Added rich library to requirements
  - Updated provider configuration
  - Simplified model selection
  - Better error handling for missing dependencies
- 🔄 Simplified configuration options:
  - Removed host and personality options from config command
  - Streamlined provider configuration process

### Fixed
- 🐛 Fixed file encoding issues with generated files
- 🐛 Fixed line ending inconsistencies
- 🐛 Fixed invisible character issues in code files
- 🐛 Fixed markdown rendering in terminals
- 🐛 Fixed file permission issues
- 🐛 Config: Fixed model persistence in configuration
- 🔒 Security: Improved API key handling
- 🚀 Performance: Optimized provider initialization

### Deprecated
- ⚠️ Old write command syntax with type flag
- ⚠️ Direct file output without view command

### Security
- 🔒 Improved file permission handling
- 🔒 Better API key management
- 🔒 Safer file operations

## [1.0.0] - 2025-02-23

### Added
- ✨ Providers: Added DeepSeek provider support
- ✨ Providers: Added OpenRouter provider with free model access
- 🔐 Config: Added environment variable support for API keys
- 📝 Docs: Added .env.template for easy configuration
- 🎨 UI: Added ANSI art and color support
- 🛠️ Utils: Added GPU and Docker utilities

### Changed
- 🔧 Architecture: Reorganized project structure into modules
- 🔄 Providers: Updated model lists with latest versions
  - OpenAI: Added O-series models (4O, O3, O1)
  - Anthropic: Updated to Claude 3.5 models (Sonnet, Haiku, Opus)
  - Google: Updated to Gemini 1.5 models with version aliases
  - DeepSeek: Added v1 models with extended context
  - OpenRouter: Added free model access
- 🎯 Core: Improved error handling and fallbacks
- 📚 Docs: Enhanced documentation with environment setup guide

### Fixed
- 🐛 Config: Fixed model persistence in configuration
- 🔒 Security: Improved API key handling
- 🚀 Performance: Optimized provider initialization

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

[unreleased]: https://github.com/sizzlebop/cliche/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/sizzlebop/cliche/releases/tag/v0.1.0
