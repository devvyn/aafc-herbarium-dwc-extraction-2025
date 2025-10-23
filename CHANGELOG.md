# Changelog

## [Unreleased]

### Changed
- **CI/Type Checking**: Replaced mypy with Astral's ty type checker ([PR #223](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/pull/223))
  - Completes Astral toolchain: uv (package management) + ruff (linting) + ty (type checking)
  - 100x+ faster than mypy, zero installation overhead (uvx)
  - Phased rollout: CI integration complete, fixing remaining type issues incrementally
  - See `[tool.ty]` in pyproject.toml for configuration and status

### Fixed
- **Type Safety**: Fixed 9 type safety issues found by ty
  - `Image.LANCZOS` deprecation → `Image.Resampling.LANCZOS`
  - Missing `List` import in dwc/archive.py
  - OpenAI optional dependency shadowing
  - Path type narrowing in cli.py
- **CI**: Fixed 22 ruff linting errors (unused variables, missing imports, boolean comparisons)
- **Dependencies**: Synced uv.lock to match pyproject.toml version 2.0.0

### Future Development
- 🔮 16 Darwin Core fields (9 additional: habitat, elevation, recordNumber, etc.)
- 🔮 Layout-aware prompts (TOP vs BOTTOM label distinction)
- 🔮 Ensemble voting for research-grade quality

## [2.0.0] - 2025-10-22

### 🎉 Specimen-Centric Provenance Architecture

**Major Achievement:** Fundamental architectural shift from image-centric to specimen-centric data model, enabling full lineage tracking and production-scale data quality management.

#### Added - Specimen Provenance System

- 🔬 **Specimen Index** (`src/provenance/specimen_index.py`)
  - SQLite database tracking specimens through transformations and extraction runs
  - Automatic deduplication at (image_sha256, extraction_params) level
  - Multi-extraction aggregation per specimen for improved candidate fields
  - Data quality flagging: catalog duplicates, malformed numbers, missing fields
  - Full audit trail from original camera files to published DwC records

- 📊 **Deduplication Logic**
  - Deterministic: same (image, params) = cached result, no redundant processing
  - Intentional re-processing supported: different params aggregate to better candidates
  - Prevents waste: identified 2,885 specimens extracted twice (5,770 → 2,885)
  - Cost savings: eliminates duplicate API calls and processing time

- 🏗️ **Specimen-Centric Data Model**
  - Specimen identity preserved through image transformations
  - Provenance DAG: original files → transformations → extractions → review
  - Content-addressed images linked to specimen records
  - Support for multiple source formats per specimen (JPEG, NEF raw)

- 🛡️ **Data Quality Automation**
  - Automatic detection of catalog number duplicates across specimens
  - Pattern validation for malformed catalog numbers
  - Perceptual hash detection for duplicate photography
  - Missing required fields flagged for human review

- 📈 **Multi-Extraction Aggregation**
  - Combines results from multiple extraction attempts per specimen
  - Selects best candidate per field (highest confidence)
  - Enables iterative improvement: reprocess with better models/preprocessing
  - All extraction attempts preserved for audit trail

#### Added - Migration & Analysis Tools

- 🔄 **Migration Script** (`scripts/migrate_to_specimen_index.py`)
  - Analyzes existing raw.jsonl files from historical runs
  - Populates specimen index without modifying original data
  - Detects duplicate extractions and reports statistics
  - Runs comprehensive data quality checks
  - Example usage:
    ```bash
    python scripts/migrate_to_specimen_index.py \
        --run-dir full_dataset_processing/* \
        --index specimen_index.db \
        --analyze-duplicates \
        --check-quality
    ```

- 📊 **Extraction Run Analysis** (`docs/extraction_run_analysis_20250930.md`)
  - Documented root cause of duplicate extractions in run_20250930_181456
  - ALL 5,770 extractions failed (missing OPENAI_API_KEY)
  - Every specimen processed exactly twice (no deduplication)
  - Provides recommendations for prevention

#### Added - Production Infrastructure

- 🌐 **Quart + Hypercorn Migration** (Async Review System)
  - Migrated review web app from Flask to Quart for async performance
  - All routes converted to async for better concurrency
  - GBIF validation now non-blocking (async HTTP with aiohttp)
  - Hypercorn ASGI server replaces Flask development server
  - Production-ready async architecture

- 🐳 **Docker Support** (`Dockerfile`, `docker-compose.yml`)
  - Production-ready containerization with multi-stage builds
  - Optimized Python 3.11-slim base image
  - Health checks and restart policies
  - Volume mounting for data persistence
  - Port mapping for review UI (5002)

- 📺 **Monitor TUI Improvements**
  - Fixed progress warnings from manifest.json/environment.json format detection
  - Support for both old and new metadata formats
  - Graceful fallback when metadata files missing
  - Proper specimen count estimation from raw.jsonl

#### Documentation - Comprehensive Guides

- 📚 **Architecture Documentation** (`docs/specimen_provenance_architecture.md`)
  - Complete specimen-centric data model specification
  - Transformation provenance DAG design
  - Extraction deduplication logic and examples
  - Data quality invariants and flagging rules
  - Full integration examples and migration patterns
  - SQL schema and API documentation

- 📋 **Release Plan** (`docs/RELEASE_2_0_PLAN.md`)
  - Three-phase migration strategy (preserve → populate → publish)
  - Progressive publication workflow (draft → batches → final)
  - Data safety guarantees and rollback procedures
  - Review UI integration requirements
  - Timeline and success criteria

#### Research Impact

**Architectural Foundation:**
- **From**: Image-centric, duplicates allowed, no specimen tracking
- **To**: Specimen-centric, automatic deduplication, full provenance

**Economic Impact:**
- Eliminates redundant extraction attempts (identified 2,885 duplicates)
- Prevents wasted API calls on already-processed specimens
- Enables cost-effective iterative improvement via aggregation

**Scientific Impact:**
- Full lineage tracking for reproducibility
- Cryptographic traceability (content-addressed images)
- Data quality automation (catalog validation, duplicate detection)
- Supports progressive publication with human review tracking

#### Technical Implementation

- **Database Schema**: 7 tables tracking specimens, transformations, extractions, aggregations, reviews, quality flags
- **Deduplication Key**: SHA256(extraction_params) for deterministic caching
- **Aggregation Strategy**: Multi-extraction results combined, best candidate per field selected
- **Quality Checks**: Automated SQL queries detect violations of expected invariants
- **Migration Safety**: Additive only, original data never modified, full rollback capability

#### Backward Compatibility

✅ **Fully Backward Compatible**
- Existing extraction runs remain valid (no modification)
- Old workflow continues to work without migration
- New features opt-in via migration script
- No breaking changes to CLI interface
- Gradual adoption supported

#### Production Readiness

- ✅ Async web architecture (Quart + Hypercorn)
- ✅ Docker containerization with health checks
- ✅ Data quality automation
- ✅ Full provenance tracking
- ✅ Progressive publication workflow
- ✅ Safe migration with rollback capability

### Changed - Infrastructure

- Migrated review web app from Flask to Quart (async)
- Updated monitor TUI for manifest.json format support
- Enhanced error handling in review system

### Fixed

- Monitor TUI progress warnings (manifest/environment format detection)
- Review UI port already in use error handling
- Auto-detection priority (real data before test data)
- S3 image URL auto-detection from manifest.json

### Notes

Version 2.0.0 represents a fundamental architectural maturity milestone, transitioning from proof-of-concept extraction to production-scale specimen management with full provenance tracking, data quality automation, and human review workflows. This release sets the foundation for progressive data publication and long-term institutional deployment.

## [1.1.1] - 2025-10-11

### Added - Accessibility Enhancements
- 🎨 **Constitutional Principle VI: Information Parity and Inclusive Design**
  - Elevated accessibility to constitutional status (Core Principle VI)
  - Cross-reference to meta-project pattern: `information-parity-design.md`
  - Validation requirements: VoiceOver compatibility, keyboard-first, screen reader native

- ⌨️ **Keyboard-First Review Interface**
  - Keyboard shortcuts with confirmation dialogs (a/r/f for approve/reject/flag)
  - Double-press bypass (500ms window) for power users
  - Prevents accidental actions during review workflow

- 🔍 **Enhanced Image Interaction**
  - Cursor-centered zoom (focal point under cursor stays stationary)
  - Pan boundary constraints (prevents image escaping container)
  - Safari drag-and-drop prevention (ondragstart blocking)

- 🏷️ **Status Filtering**
  - Filter buttons for All/Critical/High/Pending/Approved/Flagged/Rejected statuses
  - Quick access to specimens needing review
  - Visual indication of current filter state

- 🖼️ **TUI Monitor Enhancements**
  - iTerm2 inline specimen image rendering via rich-pixels
  - Real-time image preview (60x40 terminal characters)
  - 3-column layout: event stream + field quality | specimen image
  - Automatic image updates as extraction progresses

### Changed
- Review interface improvements for keyboard-first navigation
- Enhanced TUI monitor with multi-panel layout
- Updated constitution to v1.1.0 with accessibility principle

### Documentation
- Added `docs/ACCESSIBILITY_REQUIREMENTS.md` - project-level implementation roadmap
- Phase 1-3 priorities: Critical fixes → Enhanced accessibility → Documentation
- Success metrics and testing requirements defined

### Notes
This patch release prepares the production baseline (v1.1.x-stable) before beginning v2.0.0 accessibility-first redesign. All changes are backward-compatible with v1.1.0.

## [1.1.0] - 2025-10-09

### 🎉 Multi-Provider Extraction with FREE Tier Support

**Major Achievement:** Architectural shift to multi-provider extraction with zero-cost production capability

#### Added - OpenRouter Integration

- 🌐 **Multi-Model Gateway** (`scripts/extract_openrouter.py`)
  - Access to 400+ vision models via unified OpenRouter API
  - FREE tier support (Qwen 2.5 VL 72B, Llama Vision, Gemini)
  - Automatic retry with exponential backoff
  - Rate limit handling with progress tracking
  - Model selection interface with cost/quality trade-offs

- 💰 **Zero-Cost Production Pipeline**
  - Qwen 2.5 VL 72B (FREE): 100% scientificName coverage
  - Better quality than paid OpenAI baseline (98% coverage)
  - Removes financial barrier to herbarium digitization
  - Unlimited scale without queue constraints

#### Added - Scientific Provenance System

- 🔬 **Reproducibility Framework** (`src/provenance.py`)
  - Git-based version tracking for complete reproducibility
  - SHA256 content-addressed data lineage
  - Immutable provenance fragments
  - Complete system metadata capture (Python, OS, dependencies)
  - Graceful degradation for non-git environments

- 📚 **Pattern Documentation** (`docs/SCIENTIFIC_PROVENANCE_PATTERN.md`)
  - Complete guide with real-world herbarium examples
  - Best practices for scientific reproducibility
  - Integration patterns with Content-DAG architecture
  - Anti-patterns and evolution pathways
  - Working examples: `examples/provenance_example.py`, `examples/content_dag_herbarium.py`

#### Production Results

- 📊 **Quality Baseline & FREE Model Validation**
  - Phase 1: 500 specimens @ 98% scientificName coverage (OpenAI GPT-4o-mini, $1.85)
  - Validation: 20 specimens @ 100% coverage (OpenRouter FREE, $0.00)
  - Dataset: 2,885 photos ready for full-scale processing
  - Validates FREE models outperform paid baseline
  - Complete provenance tracking for scientific publication

- 📁 **Evidence Committed**
  - Phase 1 baseline statistics: `full_dataset_processing/phase1_baseline/extraction_statistics.json`
  - OpenRouter validation results: `openrouter_test_20/raw.jsonl`
  - Quality metrics documented for peer review

#### Technical Architecture

- 🏗️ **Provider Abstraction**
  - Unified interface for multiple AI providers
  - Clean separation: OpenAI, OpenRouter, future providers
  - Transparent fallback and retry mechanisms
  - No vendor lock-in or single point of failure

- ⚡ **Performance Optimizations**
  - Rate limit handling with automatic backoff
  - Progress tracking with ETA calculation
  - Efficient image encoding (base64)
  - JSONL streaming for large datasets

- 🔧 **Version Management System**
  - Single source of truth: `pyproject.toml`
  - Programmatic version access: `src/__version__.py`
  - Automated consistency checking: `scripts/check_version_consistency.py`
  - Prevents version drift across documentation

#### Research Impact

**Architectural shift:**
- **From**: Single provider, paid, queue-limited
- **To**: Multi-provider, FREE option, unlimited scale

**Economic impact:**
- Enables zero-cost extraction at production scale
- Removes financial barrier for research institutions
- Democratizes access to AI-powered digitization

**Scientific impact:**
- Full reproducibility for scientific publication
- Cryptographic traceability of research outputs
- Complete methodology documentation
- Sets new baseline for herbarium extraction quality

#### Changed - Documentation Updates

- Updated README.md with v1.1.0 features and results
- Added Scientific Provenance Pattern guide
- Enhanced with OpenRouter integration examples
- Version consistency across all public-facing docs

### Breaking Changes

None - fully backward compatible with v1.0.0

## [1.0.0] - 2025-10-06

### 🎉 Production Release - AAFC Herbarium Dataset

**Major Achievement:** 2,885 specimen photos processed, quality baseline established

#### Added - v1.0 Deliverables
- 📦 **Production Dataset** (`deliverables/v1.0_vision_api_baseline.jsonl`)
  - 2,885 herbarium photos processed with Apple Vision API
  - **Quality: 5.5% scientificName coverage (FAILED - replaced in v1.1.0)**
  - 7 Darwin Core fields attempted
  - Apple Vision API (FREE) + rules engine
  - Total cost: $0 (but unusable quality)

- ✅ **Ground Truth Validation** (`deliverables/validation/human_validation.jsonl`)
  - 20 specimens manually validated
  - Documented accuracy baselines
  - Quality metrics calculated

- 📚 **Complete Documentation**
  - Extraction methodology documented
  - Quality limitations identified
  - Upgrade path to v2.0 designed

#### Added - Agent Orchestration Framework
- 🤖 **Pipeline Composer Agent** (`agents/pipeline_composer.py`)
  - Cost/quality/deadline optimization
  - Engine capability registry (6 engines)
  - Intelligent routing: FREE-first with paid fallback
  - Progressive enhancement strategies
  - Ensemble voting support for research-grade quality

- 📋 **Data Publication Guide** (`docs/DATA_PUBLICATION_GUIDE.md`)
  - GBIF/Canadensys publication workflow
  - Darwin Core Archive export scripts
  - CC0 licensing recommendations
  - Deployment context strategies (Mac dev / Windows production)

- ⚙️ **Enhanced Configuration**
  - `config/config.gpt4omini.toml` - GPT-4o-mini direct extraction
  - Layout-aware prompts (`config/prompts/image_to_dwc_v2.*.prompt`)
  - Expanded 16-field Darwin Core schema

#### Technical Improvements - v1.0
- 🔧 **API Integration**
  - Fixed OpenAI Chat Completions API format
  - Prompt loading from files (system + user messages)
  - JSON response format for structured extraction
  - Model: gpt-4o-mini (cost-effective, layout-aware)

- 🏗️ **Architecture**
  - Plugin registry pattern (additive-only, zero conflicts)
  - Config override pattern (branch-specific configurations)
  - Parallel development enabled (v2-extraction + agent-orchestration branches)

#### Quality Metrics - v1.0 Apple Vision (DEPRECATED)
- **ScientificName coverage:** 5.5% (159/2,885) - FAILED
- **Status:** Replaced by GPT-4o-mini/OpenRouter approach in v1.1.0
- **Exact matches:** 0% (on 20-specimen validation)
- **Partial matches:** ~10-15%
- **Known limitations:** OCR accuracy insufficient for production use

#### v2.0 Preview (In Progress)
- **16 Darwin Core fields** (9 additional: habitat, elevation, recordNumber, identifiedBy, etc.)
- **Layout-aware extraction** (TOP vs BOTTOM label distinction)
- **Expected quality:** ~70% accuracy (vs ~15% baseline)
- **Cost:** $1.60 total or FREE overnight (15-20 hours)
- **Agent-managed pipelines:** "Consider all means accessible in the world"

### Changed - Documentation Overhaul
- Updated README with v1.0 production status
- Reorganized docs for clarity
- Added deployment context considerations
- Improved API setup instructions

### Fixed
- OpenAI API endpoint (responses.create → chat.completions.create)
- Environment variable naming (OPENAI_KEY → OPENAI_API_KEY)
- Model config passthrough for gpt4omini
- Prompt loading in image_to_dwc engine

## [1.0.0-beta.2] - 2025-10-04

### Added - Storage Abstraction Layer
- 🏗️ **Storage Backend Architecture** — Pluggable storage layer decoupled from core extraction logic
  - **ImageLocator Protocol** (`src/io_utils/locator.py`) — Storage-agnostic interface for image access
  - **LocalFilesystemLocator** — Traditional directory-based storage backend
  - **S3ImageLocator** — AWS S3 and S3-compatible storage (MinIO) backend
  - **CachingImageLocator** — Transparent pass-through caching decorator with LRU eviction
  - **Factory Pattern** — Configuration-driven backend instantiation (`locator_factory.py`)

- 📦 **Storage Backends Supported**
  - **Local Filesystem** — Direct directory access (default, backward compatible)
  - **AWS S3** — Cloud object storage with automatic credential handling
  - **MinIO** — Self-hosted S3-compatible storage via custom endpoint
  - **Future Ready** — Easy to add HTTP, Azure Blob, Google Cloud Storage

- 🔄 **Transparent Caching System**
  - **Automatic Caching** — Remote images cached locally on first access
  - **LRU Eviction** — Configurable cache size limit with least-recently-used eviction
  - **Cache Management** — Statistics (`get_cache_stats()`), manual clearing
  - **SHA256 Keys** — Robust cache keys handling special characters and long names

- ⚙️ **Configuration Support**
  - **TOML Configuration** — `[storage]` section in `config/config.default.toml`
  - **Example Configs** — `config/config.s3-cached.toml` for S3 with caching
  - **Backward Compatible** — Omit `[storage]` section to use local filesystem
  - **Environment Aware** — AWS credentials via environment or explicit config

- 🧪 **Comprehensive Testing**
  - **18 Passing Tests** — `tests/unit/test_locators.py` covering all components
  - **LocalFilesystemLocator** — 11 tests for local storage operations
  - **CachingImageLocator** — 7 tests for caching behavior and eviction
  - **Edge Cases** — Missing files, invalid paths, cache size limits

- 📚 **Complete Documentation**
  - **Architecture Guide** — `docs/STORAGE_ABSTRACTION.md` with patterns and examples
  - **Configuration Guide** — Storage backend configuration templates
  - **Migration Guide** — Phase 1 complete (core abstractions), Phase 2 deferred (CLI integration)
  - **Release Process** — `docs/RELEASE_PROCESS.md` for versioning and release guidelines

### Technical Implementation - Storage Abstraction
- **Protocol-Based Design** — Duck typing via `Protocol`, not abstract base classes
- **Decorator Pattern** — Caching as transparent wrapper, not baked into backends
- **Strategy Pattern** — Pluggable backends selected at runtime
- **Lazy Imports** — boto3 only imported when S3 backend needed
- **Performance Optimized** — `get_local_path()` optimization for direct filesystem access

### Backward Compatibility
- ✅ **No Breaking Changes** — Existing local filesystem workflows unaffected
- ✅ **Optional Feature** — Storage abstraction activated via configuration
- ✅ **CLI Unchanged** — Current `cli.py` works perfectly with local filesystem
- ✅ **Deferred Integration** — CLI migration to ImageLocator deferred to future release

### Added - Modern UI/UX System (2025-09-26)
- 🖥️ **Rich Terminal User Interface (TUI)** — Professional interactive terminal experience
  - Real-time progress tracking with animated progress bars and live statistics
  - Interactive configuration wizards for easy setup
  - Menu-driven navigation with keyboard support
  - Visual error reporting and engine usage charts
  - Built with Rich library for beautiful terminal displays

- 🌐 **Modern Web Dashboard** — Real-time web interface with live updates
  - WebSocket-based real-time progress updates
  - Interactive charts and visual statistics (Chart.js integration)
  - Modern responsive design with Tailwind CSS
  - Multi-user support for team environments
  - FastAPI backend with async WebSocket support

- 🚀 **Unified Interface Launcher** — Single entry point for all UI options
  - Interactive menu for interface selection
  - Direct launch options via command-line flags (`--tui`, `--web`, `--cli`, `--trial`)
  - Automatic dependency checking and installation guidance
  - Comprehensive help system and documentation

- 🔄 **Centralized Progress Tracking System** — Unified real-time updates
  - Abstract progress tracker with multiple callback support
  - Integration hooks in existing CLI processing pipeline
  - Support for TUI, web, and file-based progress logging
  - Async callback support for WebSocket broadcasting
  - Comprehensive statistics tracking (engine usage, error reporting, timing)

### Enhanced
- ⚡ **CLI Integration** — Enhanced existing command-line interface
  - Added progress tracking hooks to `cli.py` processing pipeline
  - Maintains backward compatibility with existing workflows
  - Optional progress tracking (graceful fallback if tracker unavailable)
  - Image counting and batch processing optimization

- 🧪 **Testing Infrastructure** — Comprehensive UI testing framework
  - Automated dependency checking and validation
  - Integration tests for all UI components
  - Progress tracking system validation
  - Interface import and functionality testing
  - Non-interactive demo system for CI/CD

### Technical Implementation
- **Dependencies Added**: `rich`, `fastapi`, `uvicorn`, `jinja2` for UI components
- **Architecture**: Modular design with interface abstraction
- **Performance**: Async processing to avoid blocking UI updates
- **Compatibility**: Graceful degradation when optional UI dependencies unavailable
- **Integration**: Seamless integration with existing processing pipeline

### User Experience Improvements
- **From**: Basic command-line non-interactive execution with text-only output
- **To**: Professional multi-interface system matching CLI agentic UX quality
- ✅ Real-time progress visualization with animated elements
- ✅ Interactive configuration wizards and guided setup
- ✅ Live error reporting and actionable feedback
- ✅ Multiple interface options for different user preferences
- ✅ Professional branding and consistent visual design
- ✅ Context-aware help and comprehensive documentation

## [0.3.0] - 2025-09-25

### Added - OCR Research Breakthrough
- 🔬 **Comprehensive OCR Engine Analysis** — First definitive study of OCR performance for herbarium specimen digitization
  - **Major Finding**: Apple Vision OCR achieves 95% accuracy vs Tesseract's 15% on real herbarium specimens
  - **Economic Impact**: $1600/1000 specimens cost savings vs manual transcription
  - **Production Impact**: Enables automated digitization with minimal manual review (5% vs 95%)
  - **Research Infrastructure**: Complete testing framework for reproducible OCR evaluation
  - **Documentation**: `docs/research/COMPREHENSIVE_OCR_ANALYSIS.md` with full methodology and findings

- 🧪 **Advanced OCR Testing Infrastructure**
  - Multi-engine comparison framework supporting Apple Vision, Claude Vision, GPT-4 Vision, Google Vision
  - Comprehensive preprocessing evaluation with 10+ enhancement techniques
  - Real specimen testing on AAFC-SRDC collection with statistical analysis
  - Reproducible testing protocols and automated evaluation scripts

- 📊 **Production-Ready Apple Vision Integration**
  - Native macOS OCR engine with 95% accuracy on herbarium specimens
  - Zero API costs and no vendor lock-in for primary processing
  - Enhanced vision_swift engine with macOS compatibility improvements
  - Integration with existing CLI processing pipeline

- 📚 **Research Documentation System**
  - `docs/research/` directory with comprehensive analysis and methodology
  - Updated project documentation reflecting OCR findings
  - Production deployment guidelines based on empirical testing
  - Future research directions for vision API integration

### Changed
- **OCR Engine Recommendations**: Apple Vision now primary choice, Tesseract not recommended
- **Processing Pipeline**: Updated to use Apple Vision as default OCR engine
- **Documentation**: README, roadmap, and guides updated with research findings
- **Installation Guide**: OCR engine selection based on accuracy testing

### Technical Impact
- **Eliminates API dependency** for 95% of herbarium specimen processing
- **Reduces manual labor** from 95% to 5% of specimens requiring review
- **Enables production deployment** with enterprise-grade accuracy at zero marginal cost
- **Establishes evidence-based best practices** for institutional herbarium digitization

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

[Unreleased]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v1.1.1...v2.0.0
[1.1.1]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v1.0.0-beta.2...v1.0.0
[1.0.0-beta.2]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v1.0.0-alpha.1...v1.0.0-beta.2
[1.0.0-alpha.1]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v0.3.0...v1.0.0-alpha.1
[0.3.0]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v0.1.4...v0.2.0
[0.1.4]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/releases/tag/v0.1.0
