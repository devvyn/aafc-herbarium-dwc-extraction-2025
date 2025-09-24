# Herbarium OCR to Darwin Core

A toolkit for extracting text from herbarium specimen images, mapping the results to the Darwin Core standard, and recording metadata and quality-control information.

Current version: 0.1.4 – adds adaptive thresholding, GBIF verification, Darwin Core field mappings, versioned exports, and audit tracking (see [CHANGELOG.md](CHANGELOG.md)).

## Installation

This project uses a modern pyproject.toml layout and works with uv, pip, or other PEP 621–compatible tools.
Requires Python 3.11 or later (see [pyproject.toml](pyproject.toml) or [python.org](https://www.python.org/downloads/)).

Quick start (with uv)

### Bootstrap script
Installs `uv` if it's missing, syncs dependencies, copies `.env.example`, and runs linting/tests.

```bash
./bootstrap.sh
```

### Manual install
```
uv sync --dev

# Copy and edit environment secrets
cp .env.example .env

# (Optional) add extras depending on the engine(s) you need:
#   Tesseract OCR  -> brew install tesseract && uv add ".[tesseract]"
#   Apple Vision   -> macOS only: uv add ".[apple-vision]"
#   PaddleOCR      -> uv add ".[paddleocr]"
#   GPT models     -> uv add ".[gpt]"
```

### Run the tests
```
uv run pytest -q
```

With pip (classic approach)
```
pip install -e .[dev]

# Install extras manually if needed:
#   Tesseract OCR  -> brew install tesseract && pip install pytesseract
#   Apple Vision   -> macOS only: pip install pyobjc
#   PaddleOCR      -> pip install paddleocr
#   GPT models     -> pip install openai

pytest -q
```


## Command line interface

The toolkit provides two main processing commands and several utility commands:

### Core Processing Commands

```bash
# Start new processing run
python cli.py process --input PATH/TO/images --output PATH/TO/output \
    [--config CONFIG.toml] [--engine vision --engine tesseract ...]

# Resume interrupted processing
python cli.py resume  --input PATH/TO/images --output PATH/TO/output \
    [--config CONFIG.toml] [--engine vision --engine tesseract ...]

# Create versioned Darwin Core Archive
python cli.py archive --output PATH/TO/output --version 1.0.0 \
    [--filter "confidence > 0.8"] [--include-multimedia]
```

**Key options**

- `--input/-i`   – directory of JPG/PNG images to process
- `--output/-o`  – destination directory for all artifacts and databases
- `--config/-c`  – optional TOML configuration file (merged over defaults)
- `--engine/-e`  – limit to specific OCR engines (repeatable flag)
- `--filter`     – SQL-like filter for exports (e.g., "confidence > 0.7")
- `--version`    – semantic version for archive exports

**Processing behavior**:
- `process` starts a new run, processing all images in the input directory
- `resume` skips specimens whose processing status is already "done"
- Both commands save progress to SQLite databases for fault tolerance

### Utility Commands

```bash
# Validate configuration
python cli.py validate-config --config custom.toml

# Check system dependencies
python cli.py check-deps --engines tesseract,gpt,vision

# Merge multiple processing runs
python cli.py merge --inputs run1/ run2/ run3/ --output combined/

# Generate processing statistics
python cli.py stats --db output/app.db --format html
```

### Outputs

| File/DB                    | Purpose                                   | Format | Use Case |
|----------------------------|-------------------------------------------|--------|----------|
| `occurrence.csv`           | Darwin Core occurrence records            | CSV    | GBIF publishing, analysis |
| `identification_history.csv` | Taxonomic determination history         | CSV    | Nomenclatural tracking |
| `raw.jsonl`                | Per-image processing log with OCR text   | JSONL  | Debugging, audit trails |
| `manifest.json`            | Run metadata and configuration snapshot  | JSON   | Reproducibility, provenance |
| `candidates.db`            | Raw OCR results from all engines         | SQLite | Review, quality control |
| `app.db`                   | Processed specimen metadata and status   | SQLite | Pipeline management |
| `dwca_v*.zip`              | Versioned Darwin Core Archive bundles    | ZIP    | Data publication, archival |

**File descriptions**:
- **occurrence.csv**: Standards-compliant Darwin Core records ready for biodiversity databases
- **identification_history.csv**: Captures multiple taxonomic determinations per specimen
- **raw.jsonl**: Complete processing history including confidence scores and engine outputs
- **manifest.json**: Metadata about the processing run including software versions and settings
- **candidates.db**: Intermediate database for reviewing and correcting OCR results
- **app.db**: Main processing database tracking specimen status and extracted metadata

### Versioned exports

Use the archive helper to bundle Darwin Core outputs with a manifest. When
compressing exports, supply a semantic version so the ZIP file is written as
`dwca_v<version>.zip` under `output/`. The accompanying `manifest.json` captures
the timestamp, commit hash and any filter criteria for reproducibility.

## Review interfaces

Multiple review interfaces support different workflows, from quick spot-checks to comprehensive curatorial review.

### Web-based Review (Recommended)

Launch an interactive web application for reviewing OCR results:

```bash
# Basic web interface
python review_web.py --db output/candidates.db --images input/ --port 8080

# Expert mode with advanced features
python review_web.py \
  --db output/candidates.db \
  --images input/ \
  --expert-mode \
  --batch-review \
  --auto-save-interval 30
```

**Features**:
- Side-by-side image and OCR text comparison
- Confidence-based filtering and sorting
- Bulk editing and approval workflows
- GBIF taxonomic validation integration
- Export corrected data back to database

### Terminal-based Review

For command-line workflows or remote access:

```bash
# Interactive TUI for single specimens
python review.py output/candidates.db IMAGE.JPG --tui

# Batch review with filtering
python review.py output/candidates.db \
  --filter "confidence < 0.7" \
  --batch-mode \
  --export-corrections
```

### Spreadsheet Workflows

Export to Excel/CSV for institutional review processes:

```bash
# Export for review
python export_review.py \
  --db output/app.db \
  --format xlsx \
  --filter "confidence < 0.8 OR gbif_match = false" \
  --output review_package.xlsx

# Import corrections
python import_review.py \
  --db output/app.db \
  --input reviewed_corrections.xlsx \
  --validate-changes
```

**Spreadsheet features**:
- Pre-configured Darwin Core column headers
- Data validation rules
- Conditional formatting for flagged records
- Integration with institutional review processes

### Quality Control Workflows

Automated flagging and validation:

```bash
# Generate QC report
python qc/comprehensive_qc.py \
  --db output/app.db \
  --output qc_report.html \
  --include-geographic-validation \
  --include-taxonomic-validation

# Review flagged records only
python review_web.py \
  --db output/candidates.db \
  --filter "qc_flags IS NOT NULL" \
  --prioritize-types
```

See [docs/review_workflow.md](docs/review_workflow.md) for detailed review procedures and [docs/user_guide.md](docs/user_guide.md) for workflow examples.

## Configuration highlights (`config/config.default.toml`)

- **OCR** – `preferred_engine`, `enabled_engines`, `allow_gpt`, `allow_tesseract_on_macos`, `confidence_threshold`
- **GPT** – `model`, `dry_run`, `fallback_threshold`
- **Tesseract** – `oem`, `psm`, `langs`, `extra_args`
- **PaddleOCR** – `lang`
- **Preprocess** – `pipeline = ["grayscale","deskew","binarize","resize"]`, `binarize_method`, `max_dim_px`, optional `contrast_factor` (used when `"contrast"` is in the pipeline)
- **DWc mapping** – `assume_country_if_missing`, `strict_minimal_fields`, normalization toggles
- **QC** – duplicate detection (`phash_threshold`), low-confidence flagging, top-fifth scan flag
- **Processing** – `retry_limit` for failed specimens

### Configuration files and rules

See the [configuration guide](docs/configuration.md) for a tour of the `config`
directory. Mapping and normalisation helpers live in
[`config/rules`](config/rules), which currently includes placeholders for
Darwin Core mappings, institution codes, and vocabulary tables. Schema files
under [`config/schemas`](config/schemas) default to Darwin Core plus ABCD and
may be overridden in custom configurations via `dwc.schema_files`.

## Preprocessing pipeline

Preprocessing steps are registered via `preprocess.register_preprocessor`. Configure them under `[preprocess]`:

```toml
[preprocess]
pipeline   = ["grayscale", "deskew", "binarize", "resize"]
binarize_method = "adaptive"
max_dim_px = 4000
contrast_factor = 1.5  # used when "contrast" is in the pipeline
```

Prototype flows for each engine are documented in `docs/preprocessing_flows.md`.

## Engine plugins

Built‑in engines (`vision`, `tesseract`, `paddleocr`, `gpt`) register themselves when their dependencies are available. Additional engines can be added with Python entry points:

```toml
[project.entry-points."herbarium.engines"]
my_engine = "my_package.my_module"
```

Within the module, register tasks:

```python
from engines import register_task
register_task("image_to_text", "my_engine", __name__, "image_to_text")
```

Fallback policies allow engines such as GPT to take over when confidence is low.

## GPT usage and API integration

The GPT engine provides state-of-the-art OCR accuracy, especially for handwritten historical labels. It integrates with OpenAI's API using customizable prompts optimized for herbarium specimens.

### Setup and Configuration

**API Key Setup**:
```bash
# Add to .env file (never commit this file)
echo "OPENAI_API_KEY=your-api-key-here" >> .env

# Verify API access
python -c "import openai; print('API key valid')"
```

**Configuration** (in your `.toml` file):
```toml
[gpt]
model = "gpt-4-vision-preview"  # or "gpt-4o"
dry_run = false                 # Set true for testing without API calls
rate_limit_delay = 1.0         # Seconds between requests
batch_size = 10                # Process multiple images per request
fallback_threshold = 0.7       # Use GPT when other engines score below this
max_tokens = 1024              # Response length limit
temperature = 0.1              # Minimize randomness for consistent results
```

### Cost Management

**Typical costs** (subject to OpenAI pricing changes):
- Small specimens (< 1MB): $0.01-0.02 per image
- Large specimens (> 2MB): $0.02-0.05 per image
- Historical/damaged labels: $0.03-0.08 per image (may require multiple attempts)

**Cost optimization strategies**:
```toml
[gpt]
# Use GPT only for difficult cases
fallback_threshold = 0.8  # Higher threshold = less GPT usage

# Batch processing reduces API overhead
batch_size = 20

# Preprocess images to reduce size
[preprocess]
max_dim_px = 2000  # Smaller images = lower costs
```

### Prompt Customization

Prompts are stored in [`config/prompts`](config/prompts) and can be customized for your collection:

```bash
# Test prompt effectiveness
python scripts/prompt_coverage.py --mode comprehensive

# Validate custom prompts
python scripts/prompt_coverage.py --mode custom --prompt-dir ./custom-prompts/

# Benchmark prompt performance
python scripts/prompt_coverage.py --mode benchmark
```

**Custom prompt example**:
```
# config/prompts/text_to_dwc.system.prompt
You are extracting data from herbarium specimen labels for scientific databases.
Focus on: scientific names, collection dates, collector names, and localities.
Institution-specific note: Our collection focuses on [your region] flora.
```

See [docs/gpt.md](docs/gpt.md) for detailed GPT configuration and prompt optimization.

## Documentation and Getting Started

### Quick Start Guides

- **[User Guide](docs/user_guide.md)**: Step-by-step processing workflows
- **[Workflow Examples](docs/workflow_examples.md)**: Real-world institutional scenarios
- **[FAQ](docs/faq.md)**: Common questions and troubleshooting
- **[Troubleshooting Guide](docs/troubleshooting.md)**: Detailed problem resolution

### Technical Documentation

- **[Configuration Guide](docs/configuration.md)**: Detailed configuration options
- **[GPT Integration](docs/gpt.md)**: API setup and prompt optimization
- **[Database Schema](docs/database_schema.md)**: Database structure and queries
- **[Development Guide](docs/development.md)**: Contributing and extending the toolkit

### Data Standards and Quality Control

- **[Mapping and Vocabulary](docs/mapping_and_vocabulary.md)**: Darwin Core field mappings
- **[Quality Control](docs/qc.md)**: Validation and review procedures
- **[Export and Reporting](docs/export_and_reporting.md)**: Data publication workflows

### Project Management

- **[Roadmap](docs/roadmap.md)**: Upcoming features and priorities
- **[CHANGELOG](CHANGELOG.md)**: Version history and updates

## Development and Contributing

### Development Setup

```bash
# Install development dependencies
./bootstrap.sh

# Run tests
uv run pytest -q

# Format and lint code
uv run ruff check . --fix
uv run ruff format .
```

### Testing

The project includes comprehensive testing for OCR engines, data mapping, and quality control:

```bash
# Run all tests
pytest

# Test specific functionality
pytest tests/unit/test_gpt_prompts.py      # GPT prompt validation
pytest tests/unit/test_prompt_coverage.py  # Prompt coverage analysis
pytest tests/integration/                  # End-to-end workflows

# Test prompt effectiveness
python scripts/prompt_coverage.py --mode comprehensive
```

### Code Quality

- **Linting**: Ruff for code formatting and style
- **Type Checking**: Optional type hints for scientific data structures
- **Documentation**: Keep docs current with code changes
- **Testing**: Required for new OCR engines and data mappings

Consult [docs/development.md](docs/development.md) for detailed development guidelines and contribution procedures.

### Commit messages

Start each commit message with a gitmoji (see [gitmoji.dev](https://gitmoji.dev)) followed by a brief summary. This repository provides a `.gitmessage` template:

```
:sparkles: Brief summary

More detailed description...
```

Configure it locally so `git commit` pre-fills the template:

```
git config commit.template .gitmessage
```
