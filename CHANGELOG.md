# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Generic LLM API support for OpenAI and Google Gemini
- Environment variable configuration for API keys
- Example environment file (`env.example`)
- Comprehensive API key setup instructions in README
- Troubleshooting section for API key issues
- Support for all tested models: GPT-4o Mini, GPT-4o, GPT-4.1, GPT-3.5 Turbo, Gemini 2.0 Flash, Gemini 2.0 Flash Lite, Gemini 2.5 Pro, O1, O3

### Changed
- Replaced Walmart-specific LLM gateway with standard API calls
- Updated LLM evaluation to use OpenAI and Google Gemini APIs directly
- Enhanced README with detailed setup instructions
- Improved error handling for missing API keys
- Replaced Claude support with Google Gemini support
- Updated model names to align with actual tested models from results/

### Removed
- Walmart-specific authentication code (`call_llm_walmart.py`)
- Walmart gateway URLs and authentication headers
- Walmart-specific consumer IDs and keys
- Walmart artifactory references in wandb files
- Anthropic Claude support

### Fixed
- LLM evaluation now works with standard API keys
- Proper error messages for missing API keys
- Generic authentication for multiple LLM providers

## [Previous Versions]

- Initial release with Walmart-specific implementation 