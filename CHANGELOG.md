# Changelog

All notable changes to the CLIche project will be documented in this file.

## [Pre-Release Beta]

## [1.4.0] - 2025-02-28

### Added
- 🖼️ Added AI-powered image generation to image command
  - Integrated with OpenAI's DALL-E API
  - Added support for Stability AI's image generation
  - Implemented --generate option for existing image command
  - Added provider selection and model selection
  - Added style options specific to each provider
  - Implemented proper error handling with helpful guidance
  - Created dedicated configuration with --dalle-key and --stability-key
  - Added automated image storage in ~/.cliche/files/images/
- 🎨 Unified `create` command for ASCII/ANSI art generation
  - Consolidates functionality of art and ansi commands
  - Added banner mode for creating text headers
  - Improved font selection and display options
  - Maintains backward compatibility with existing commands

### Fixed
- 🔧 Improved Unsplash API key handling
  - Added multiple fallback methods for finding the API key
  - Updated error message with clearer configuration instructions
  - Fixed issues with running CLIche outside the normal environment
  - Cleaned up redundant entries in config file

### Enhanced
- 🖼️ Streamlined image viewing experience
  - Removed verbose output messages during image viewing/generation
  - Added automatic image display after generation with minimal text
  - Simplified error messages and suggestions
  - Created a cleaner, more user-friendly interface
- 🧹 Improved placeholder cleanup in document generation
  - Added specific cleanup for legacy image placeholder patterns
  - Enhanced markdown document cleaning to remove all placeholder artifacts
  - Ensured consistent cleanup across research, write, and generate commands
  - Improved document quality with cleaner output
- 🔄 Standardized image handling across research and write commands
  - Removed legacy image placeholder instructions in research command
  - Unified both commands to use AI-powered contextual image placement
  - Simplified the codebase by using consistent approach for all document generation
  - Improved user experience with cleaner output messages
- 🖼️ Extended AI-powered image placement to the generate command
  - Removed verbose prompt instructions
  - Simplified image processing logic
  - Created consistent experience across all document generation commands
  - Improved document generation quality with better formatting
- 🔄 Improved Python.org scraping with consistent styling and output
  - Added blue crawl4ai initialization text for consistency across all sites
  - Enhanced content extraction with crawl4ai integration
  - Improved file naming with timestamped JSON files matching image directories
  - Fixed error handling and fallback strategies for better reliability
  - Added clear output messaging showing where files are saved

## [1.3.4] - 2025-02-27

### Enhanced
- 🖼️ Added AI-powered contextual image placement across all document commands
  - Implemented LLM-based analysis to find optimal image placement points
  - Enhanced image handling in research, generate, and write commands
  - Images now placed at contextually relevant positions in the document
  - Added fallback to evenly distributed placement when LLM suggestions unavailable
  - Replaced confusing error messages with more user-friendly notifications

## [1.3.3] - 2025-02-27

### Fixed
- 🔧 Fixed primary web crawler functionality in research command
  - Updated to use correct crawler methods (`arun`, `aprocess_html`) available in current `crawl4ai` version
  - Improved error handling and content extraction reliability
  - Enhanced debugging information for troubleshooting
  - Better fallback behavior when primary extraction fails
- 🧩 Added crawler method detection to adapt to different `crawl4ai` versions

## [1.3.2] - 2025-02-26

### Enhanced
- 🖼️ Improved image handling in documents with direct Unsplash URLs
  - Better compatibility with all markdown viewers
  - Improved document sharing without local file dependencies
  - Standard markdown syntax for images
- 🔧 Fixed image formatting issues in HTML documents
- 📝 Updated documentation to reflect new image handling approach

### Changed
- 🔄 Modified image processing to use direct Unsplash URLs in documents instead of downloading
- 🧩 Removed non-standard markdown syntax for better compatibility

## [1.3.1] - 2025-02-26

### Enhanced
- 🔍 Improved `research` command with cleaner extraction messages
  - Removed confusing technical extraction failure messages
  - Simplified success messages for better user experience
- 📂 Enhanced file naming with automatic incremental suffixes
  - Prevents overwriting of existing files
  - Adds numbering (_1, _2, etc.) to files with the same base name
  - Works across all document generation commands (research, write, generate, scrape)
- 📝 Updated documentation to reflect new file naming convention
- 🔧 Improved code block extraction in the `scrape` command
  - Added language detection for code blocks 
  - Properly formats code blocks with appropriate language specifiers
  - Better handles nested code blocks in div containers
  - Enhanced Wikipedia content extraction with proper code block formatting

### Fixed
- 🔄 Ensured consistent messaging in the terminal during research and content extraction
- 🧩 Cleaned up output during web content processing
- 📄 Fixed markdown code block formatting issues in generated documents
  - Properly closes code blocks that were previously left open
  - Fixes broken language specifiers (e.g., ```pytho\nn → ```python)
  - Ensures proper spacing before and after code blocks
  - Improves instructions to LLM for better code block formatting

## [1.3.0] - 2025-02-25

### Added
- 🖼️ New `image` command for Unsplash integration
  - Search for high-quality, free images with various filters
  - Download images with custom dimensions
  - Proper attribution in compliance with Unsplash requirements
- 📸 Image integration for document generation commands
  - Add images to research results with `--image` option
  - Include images in generated documents from scraped content
  - Add images to content created with the `write` command
- 🔑 Unsplash API key configuration via `config --unsplash-key`
- 🗂️ Automatic local image storage in `~/.cliche/files/images/`

### Enhanced
- 📝 `write` command now supports image integration
- 🔍 `research` command with image support for better documentation
- 📄 `generate` command with image capabilities for richer documents
- 📚 Documentation updated with image command usage examples
- ⚙️ Configuration system extended to support service-specific APIs

### Changed
- 🔄 Updated dependency requirements to include Unsplash API client
- 🧩 Modified document generation to support image placeholders
- 📦 Enhanced file storage organization to include images directory

## [1.2.0] - 2025-02-25

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

## [1.1.0] - 2025-02-24

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

## [1.0.0] - 2025-02-24

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

## [1.2.1] - 2025-02-24

### Added
- 🔍 Re-implemented `search` command for finding files on your computer
  - Search by file name pattern or file type
  - Search from home directory, current directory, or root
  - Support for hidden files and depth control
  - Uses fast fd-find when available with fallback to find command
  - Improved cross-platform support

## [0.3.0] - 2025-03-01

### ✨ Added
- Completely redesigned image extraction system with modular architecture
- New `ImageExtractor` class for robust image extraction and downloading
- Specialized extractors for Wikipedia and Python.org documentation
- Crawling system with depth and multi-page support
- Content relevance filtering based on topic
- Proper separation of scraping and document generation
- Detailed console output for scraping operations
- Improved error handling and fallback mechanisms

### 🔄 Changed
- Separated scrape and generate commands for better separation of concerns
- Improved image organization by topic and domain
- Enhanced backward compatibility layer for image_scraper
- Better logging and debug information
- Updated crawler configuration for compatibility with latest crawl4ai

### 🐛 Fixed
- Fixed import issues in extractors
- Resolved parameter mismatches in extractor methods
- Fixed image download and path handling
- Addressed crawl4ai API compatibility issues

---

Made with ❤️ by Pink Pixel
Dream it, Pixel it ✨
