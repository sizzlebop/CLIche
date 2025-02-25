# Changelog

All notable changes to the CLIche project will be documented in this file.

## [1.2.0] - 2023-06-15

### Added
- ✨ New `research` command for web search integration
  - Multi-source content extraction with intelligent aggregation
  - Web-based research with query focusing
  - Document generation with organized sections
  - Toggle between snarky and professional modes
- 🕸️ New `scrape` command for targeted web scraping
  - Domain-specific content extraction
  - Topic-focused crawling with depth control
  - JSON storage of structured data
  - LLM-powered content extraction
- 📝 New `generate` command for document generation
  - Creates documents from scraped content
  - Intelligent section organization
  - Multiple output formats (markdown, HTML, PDF)
  - Professional formatting and styling
- 🧪 Helper scripts for common operations
  - `scrape.sh` for topic-based scraping
  - `generate.sh` for document generation
  - `cliche-bypass` for isolated environment execution
- 🔍 Enhanced search capabilities with DuckDuckGo integration
- 🌐 Asynchronous web crawler for efficient content gathering
- 🧠 LLM-powered content summarization and organization
- 🔧 Professional mode for formal documentation

### Enhanced
- 🚀 Installation and setup process with improved error handling
- 📚 Documentation with comprehensive command-specific guides
- 🔌 Server detection and `find` command functionalities
- 🖼️ Configuration management with additional settings
- 💾 File storage organization for research and scraped content

### Changed
- 🔄 Updated dependency requirements to include web scraping libraries
- 🎨 Improved help text and command descriptions
- 🌈 Enhanced terminal output with richer formatting
- 🔧 Refactored code architecture for better modularity

### Fixed
- 🐛 Content extraction from specific website types
- 🔧 Document generation with proper section hierarchy
- 📄 File encoding issues with certain content types
- 🚫 Rate limiting and error handling for web requests
- 🔒 Security improvements for web content processing

### Security
- 🔐 Enhanced URL validation and sanitization
- 🛡️ Improved error handling for web requests
- 🔒 Rate limiting to prevent API abuse

## [1.1.0] - 2023-03-10

### Added
- 🎨 ASCII art generation with custom fonts
- 🌈 ANSI art collection display
- 🖥️ System information display with `sysinfo` command
- 🔌 Server management with `server` command
- 📊 Enhanced response formatting

### Changed
- ⚡ Improved performance for long-running commands
- 🔧 Refactored provider management for easier switching
- 📝 Updated documentation with new features

### Fixed
- 🐛 API key handling for certain providers
- 🔧 Output formatting issues in certain terminals
- 📄 File saving with special characters in filenames

## [1.0.0] - 2023-01-15

### Added
- 🚀 Initial release with core functionality
- 🤖 Support for multiple LLM providers
  - OpenAI (GPT-4, GPT-3.5)
  - Anthropic (Claude)
  - Google (Gemini)
  - DeepSeek (Chat, Coder)
  - OpenRouter (Free models)
  - Ollama (Local models)
- ✨ Generation commands
  - `code`: Generate code in any language
  - `write`: Generate text, markdown, or HTML content
  - `view`: View generated files with proper formatting
- 🔐 Secure API key management
- 🎯 Easy provider switching
- 😏 Snarky responses and personality
- ⚙️ Configuration management
- 📁 File organization for generated content

## [1.2.1] - 2025-02-25

### Added
- 🔍 Re-implemented `search` command for finding files on your computer
  - Search by file name pattern or file type
  - Search from home directory, current directory, or root
  - Support for hidden files and depth control
  - Uses fast fd-find when available with fallback to find command
  - Improved cross-platform support

---

Made with ❤️ by Pink Pixel
Dream it, Pixel it ✨
