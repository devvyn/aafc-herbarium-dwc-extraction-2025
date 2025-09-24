# Changelog

## [Unreleased]

## [0.2.0] - 2024-09-24

### Added - Phase 1 Major Enhancements
- ✨ **Versioned DwC-A Export System** ([#158](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/158))
  - Rich provenance tracking with semantic versioning, git integration, timestamps
  - Configurable bundle formats ("rich" vs "simple")
  - Embedded manifests with file checksums and comprehensive metadata
  - New `cli.py export` command for streamlined export workflows
- ✨ **Official Schema Integration** ([#188](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/188))
  - Automatic fetching of official DwC/ABCD schemas from TDWG endpoints
  - Intelligent caching system with configurable update intervals
  - Schema validation and compatibility checking
  - `SchemaManager` class for high-level schema operations
- ✨ **Enhanced Mapping System**
  - Fuzzy matching and similarity-based mapping suggestions
  - Auto-generation of mappings from official schemas
  - Configuration-driven mapping rules with dynamic updates
  - Integration with existing mapper functionality
- ✨ **Enhanced GBIF Integration**
  - Comprehensive GBIF API client with taxonomy and locality verification
  - Configurable endpoints, retry logic, and rate limiting
  - Enhanced error handling and metadata tracking
  - Support for occurrence validation and fuzzy matching
- 📚 **Comprehensive Documentation**
  - New documentation: API reference, user guide, workflow examples, FAQ, troubleshooting
  - Schema mapping guide with practical examples
  - Enhanced export and reporting documentation
- 🧪 **Expanded Testing**
  - New unit tests for schema management and enhanced mapping
  - Integration tests for end-to-end workflows
  - Enhanced prompt coverage testing harness
  - Comprehensive test coverage for new functionality

### Enhanced
- 🔧 **Configuration System**
  - Extended configuration options for schema management, GBIF integration
  - Export format preferences and behavior settings
  - Enhanced validation and error reporting
- 🖥️ **CLI Improvements**
  - Better error handling and user feedback
  - Support for schema management operations
  - Enhanced archive creation workflows

### Infrastructure
- 🗄️ **Schema Cache**: Official schemas cached locally for offline operation
- 📦 **Package Structure**: New modules for schema management and enhanced functionality
- ⚡ **Performance**: Caching and optimization for schema operations

### Previous Changes
- :seedling: uv lockfile and bootstrap script for quick environment setup
- :label: expand mapping rules for collector numbers and field note vocabulary
- :dog: bootstrap script now runs linting and tests after syncing dependencies
- :bug: bootstrap script installs uv if missing
- :bug: avoid auto-registering unimplemented multilingual OCR engine
- :bug: normalize `[ocr].langs` for PaddleOCR, multilingual, and Tesseract engines so ISO 639-1/639-2 codes interoperate out of the box ([#138](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/138))
- :memo: outline testing and linting expectations in the development guide

## [0.1.4] - 2025-09-10 (0.1.4)

### Added
- ✨ adaptive threshold preprocessor with selectable Otsu or Sauvola binarization
- ✨ configurable GBIF endpoints via `[qc.gbif]` config section
- ✨ core Darwin Core field mappings and controlled vocabularies
- ✨ load custom Darwin Core term mappings via `[dwc.custom]` config section
- ✨ versioned Darwin Core Archive exports with run manifest
- ✨ taxonomy and locality verification against GBIF with graceful error handling
- ✨ track review bundle imports with audit entries

### Fixed
- 🐛 normalize `typeStatus` citations to lowercase using vocabulary rules
- 🐛 record review import audits in the main application database

### Docs
- 📝 document adaptive thresholding options in preprocessing and configuration guides
- 📝 document GBIF endpoint overrides in QC and configuration guides
- 📝 document custom term mappings and vocabulary examples
- 📝 describe versioned exports in README and export guide

## [0.1.3] - 2025-09-08 (0.1.3)

### Docs
- 📝 mark developer documentation milestone; refine roadmap and TODO priorities (non-breaking, optional upgrade)

## [0.1.2] - 2025-09-03 (0.1.2)

### Added
- support GPT image-to-Darwin Core extraction with default prompts
- :gear: configurable task pipeline via `pipeline.steps`
- :sparkles: interactive candidate review TUI using Textual
- :sparkles: lightweight web review server for OCR candidate selection
- :sparkles: export/import review bundles with manifest and semantic versioning
- :sparkles: spreadsheet utilities for Excel and Google Sheets review
- :sparkles: automatically open image files when reviews start with optional `--no-open` flag

### Fixed
- guard against non-dict GPT responses to avoid crashes
- handle multiple reviewer decisions per image when importing review bundles

### Changed
- :recycle: load role-based GPT prompts and pass messages directly to the API

### Docs
- 📝 outline review workflow for TUI, web, and spreadsheet interfaces

## [0.1.1] - 2025-09-02 (0.1.1)

### Added
- :recycle: Load Darwin Core fields from configurable schema files and parse URIs
- :card_file_box: Adopt SQLAlchemy ORM models for application storage
- :lock: Support `.env` secrets and configurable GPT prompt templates

### Changed
- :memo: Document configuration, rules and GPT setup
- :package: Move prompt templates under `config/prompts`

### Removed
- :fire: Legacy hard-coded prompt paths

## [0.1.0] - 2025-09-01 (0.1.0)

### Added
- :construction: project skeleton with CLI and configurable settings
- :package: wheel packaging with importlib-based config loading
- :sparkles: DWC schema mapper and GPT-based extraction modules
- :crystal_ball: Vision Swift and Tesseract OCR engines with pluggable registry
- :hammer_and_wrench: preprocessing pipeline, QC utilities, and GBIF verification stubs
- :card_file_box: SQLite database with resume support and candidate review CLI
- :memo: developer documentation, sample Darwin Core Archive, and comprehensive tests

### Changed
- :loud_sound: replace print statements with logging

### Fixed
- :bug: handle missing git commit metadata
- :bug: correct mapper schema override

[Unreleased]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v0.1.4...HEAD
[0.1.4]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/releases/tag/v0.1.0
