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

Two subcommands drive the pipeline:

```bash
python cli.py process --input PATH/TO/images --output PATH/TO/output \
    [--config CONFIG.toml] [--engine vision --engine tesseract ...]

python cli.py resume  --input PATH/TO/images --output PATH/TO/output \
    [--config CONFIG.toml] [--engine vision --engine tesseract ...]
```

**Key options**

- `--input/-i`   – directory of JPG/PNG images
- `--output/-o`  – destination for all artifacts
- `--config/-c`  – optional TOML file merged over `config/config.default.toml`
- `--engine/-e`  – limit OCR engines (repeatable flag)

`process` starts a new run; `resume` skips specimens whose processing status is already “done”.

### Outputs

| File/DB                    | Purpose                                   |
|----------------------------|-------------------------------------------|
| `occurrence.csv`           | Darwin Core records                       |
| `identification_history.csv` | Identification history rows              |
| `raw.jsonl`                | Per-image event log (OCR text, flags, etc.) |
| `manifest.json`            | Run metadata and configuration snapshot   |
| `candidates.db`            | Raw OCR candidates                        |
| `app.db`                   | Specimen metadata and processing state    |

### Versioned exports

Use the archive helper to bundle Darwin Core outputs with a manifest. When
compressing exports, supply a semantic version so the ZIP file is written as
`dwca_v<version>.zip` under `output/`. The accompanying `manifest.json` captures
the timestamp, commit hash and any filter criteria for reproducibility.

## Review interfaces

Review exported candidates using the text-based UI, a browser, or spreadsheets. Each option operates on a review bundle rather than the main database.

- Text UI: `python review.py output/candidates.db IMAGE.JPG --tui`
- Web UI: `python review_web.py --db output/candidates.db --images output`
- Spreadsheet flow: see [`io_utils/spreadsheets.py`](io_utils/spreadsheets.py)

See [docs/review_workflow.md](docs/review_workflow.md) for OS-specific commands and import steps. For a minimal CLI that handles a single image, run [`review.py`](review.py).

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

## GPT usage and secrets

The GPT engine calls the OpenAI API using prompts stored in
[`config/prompts`](config/prompts). Configure model settings in the
`[gpt]` section of your configuration file. Load API credentials from a
`.env` file or another secrets manager via the `OPENAI_API_KEY` environment
variable—never commit keys to the repository. See [docs/gpt.md](docs/gpt.md)
for details.

## Development

Consult [docs/development.md](docs/development.md) for development guidelines.
The project [roadmap](docs/roadmap.md) outlines upcoming features, priorities,
and timelines.

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
