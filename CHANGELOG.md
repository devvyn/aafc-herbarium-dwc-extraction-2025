# Changelog

## [Unreleased]

### Added
- support GPT image-to-Darwin Core extraction with default prompts
- :gear: configurable task pipeline via `pipeline.steps`
- :sparkles: interactive candidate review TUI using Textual
- :sparkles: lightweight web review server for OCR candidate selection
- :sparkles: export/import review bundles with manifest and semantic versioning

### Fixed
- guard against non-dict GPT responses to avoid crashes

### Changed
- :recycle: load role-based GPT prompts and pass messages directly to the API

## [0.1.1] - 2025-09-02

### Added
- :recycle: Load Darwin Core fields from configurable schema files and parse URIs
- :card_file_box: Adopt SQLAlchemy ORM models for application storage
- :lock: Support `.env` secrets and configurable GPT prompt templates

### Changed
- :memo: Document configuration, rules and GPT setup
- :package: Move prompt templates under `config/prompts`

### Removed
- :fire: Legacy hard-coded prompt paths

## [0.1.0] - 2025-09-01

- document configuration files and GPT usage
- outline development stubs and placeholders
- add schema selection options in configuration
- record default Darwin Core namespace and note dynamic loading
- bump project version to 0.1.0

[Unreleased]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/releases/tag/v0.1.0
