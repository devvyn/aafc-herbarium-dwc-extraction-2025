# Changelog

## [Unreleased] (0.1.4)

### Added
- ✨ adaptive threshold preprocessor with selectable Otsu or Sauvola binarization
- ✨ configurable GBIF endpoints via `[qc.gbif]` config section
- ✨ core Darwin Core field mappings and controlled vocabularies
- ✨ load custom Darwin Core term mappings via `[dwc.custom]` config section
- ✨ versioned Darwin Core Archive exports with run manifest

### Fixed
- 🐛 normalize `typeStatus` citations to lowercase using vocabulary rules

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

[Unreleased]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/releases/tag/v0.1.0
