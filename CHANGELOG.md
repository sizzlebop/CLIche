# Changelog

All notable changes to the CLIche project will be documented in this file.

## [Pre-Release Beta]

## [Unreleased]
### Added
- 🎨 New interactive ANSI art drawing command:
  - Added `draw` command with intuitive TUI interface
  - Implemented mouse-based drawing with color selection
  - Added multiple drawing tools (brush, eraser, fill, text)
  - Created undo/redo functionality
  - Implemented character/brush selection
  - Added canvas saving to ANSI files
  - Added keyboard shortcuts for common operations
  - Created comprehensive documentation in docs/DRAW_COMMAND_README.md
  - Integrated with Durdraw for professional drawing capabilities
  - Added both ASCII art mode (text characters) and ANSI art mode (colored blocks)
  - Implemented frame-based animation with playback controls
  - Added command options for width, height, and output file
  - Provided interface for copy/paste operations and selections
  - Added canvas resizing capabilities through command line and keyboard shortcuts
- 🔍 Enhanced web scraping capabilities in the `scrape` command:
  - Added `--max-pages` parameter to control the total number of pages scraped
  - Improved crawler configuration for proper multi-page content extraction
  - Enhanced content extraction algorithm to prioritize larger, more relevant chunks
  - Better debug output with detailed information about the scraping process
  - Fixed issues with depth-based link following and content accumulation
  - Implemented scaled content limits based on depth (100,000 chars × depth)
  - Added clear console messages about crawler settings and content extraction
- 🔍 Improved web scraping capabilities:
  - Increased character limit in general extractor to 1 million chars
  - Increased character limit in research command to 100K chars per page
  - Added browser-based rendering for better JavaScript content extraction
  - Implemented detailed progress output with timing information
  - Enhanced console output to match research command style
- 📚 Updated documentation for scraping and research commands
- 🗺️ Added future plans for specialized blog/medium extractor
- 🎛️ Added flexible dual command pattern:
  - Allow using commands in both flag style (--option) and subcommand style
  - Implemented in config-manager command
  - Added utility helpers for easy implementation in other commands
  - Improved command-line usability and flexibility
  - Updated documentation with usage examples
- 🔍 Enhanced web scraping capabilities in the `scrape` command:
  - Added `--max-pages` parameter to control the total number of pages scraped
  - Improved crawler configuration for proper multi-page content extraction
  - Enhanced content extraction algorithm to prioritize larger, more relevant chunks
  - Better debug output with detailed information about the scraping process
  - Fixed issues with depth-based link following and content accumulation
  - Implemented scaled content limits based on depth (100,000 chars × depth)
  - Added clear console messages about crawler settings and content extraction

### Changed
- Refactored general extractor to use direct browser rendering
- Improved error handling and fallback mechanisms
- Enhanced content extraction quality for JavaScript-heavy sites
- Updated README.md with new draw command information and examples
- Updated CLICHE_PLAN.md to mark the drawing tool implementation as complete
- Updated config-manager command to support both --flag and subcommand styles
- ⚙️ Optimized token limits for all providers based on cost and capabilities:
  - Increased OpenAI and Anthropic limits to 20,000 tokens (balanced for cost)
  - Increased Google limit to 64,000 tokens (higher since it's more affordable)
  - Maintained DeepSeek limit at 8,192 tokens (model limitation)
  - Kept OpenRouter limit at 100,000 tokens for maximum flexibility
  - Increased Ollama limit to 100,000 tokens (for local models)

### Fixed
- Resolved browser initialization issues with crawl4ai
- Fixed character limit inconsistencies between commands
- Improved image extraction reliability
- Fixed config-manager command flags (--show, --create, --backup, etc.)

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
  - Updated to use correct crawler methods (`arun`, `aprocess_html`) available in current `