# Herbarium OCR to Darwin Core

A toolkit for extracting text from herbarium specimen images, mapping the results to the Darwin Core standard, and recording metadata and quality-control information.

## Installation

```bash
pip install -e .
# Add optional dependencies for engines you plan to use:
#   Tesseract OCR  -> tesseract-ocr and pytesseract
#   Apple Vision   -> macOS + pyobjc
#   GPT models     -> openai
pytest -q  # run the unit tests
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

## Configuration highlights (`config/config.default.toml`)

- **OCR** – `preferred_engine`, `enabled_engines`, `allow_gpt`, `allow_tesseract_on_macos`, `confidence_threshold`
- **GPT** – `model`, `dry_run`, `fallback_threshold`
- **Tesseract** – `oem`, `psm`, `langs`, `extra_args`
- **Preprocess** – `pipeline = ["grayscale","deskew","binarize","resize"]`, `max_dim_px`, `contrast_factor`
- **DWc mapping** – `assume_country_if_missing`, `strict_minimal_fields`, normalization toggles
- **QC** – duplicate detection (`phash_threshold`), low-confidence flagging, top-fifth scan flag
- **Processing** – `retry_limit` for failed specimens

## Preprocessing pipeline

Preprocessing steps are registered via `preprocess.register_preprocessor`. Configure them under `[preprocess]`:

```toml
[preprocess]
pipeline   = ["grayscale", "deskew", "binarize", "resize"]
max_dim_px = 4000
```

Prototype flows for each engine are documented in `docs/preprocessing_flows.md`.

## Engine plugins

Built‑in engines (`vision`, `tesseract`, `gpt`) register themselves when their dependencies are available. Additional engines can be added with Python entry points:

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
