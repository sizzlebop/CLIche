# Changelog

All notable changes to CLIche will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- 🎨 Improved write command output:
  - Shows LLM's explanation/commentary in terminal
  - Only saves code to file when generating code
  - Added progress indicators for better UX
  - Fixed code block extraction for more reliable results

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
