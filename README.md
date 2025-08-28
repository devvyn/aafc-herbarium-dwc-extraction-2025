# Herbarium OCR to Darwin Core

Toolkit for extracting text from herbarium specimen images and mapping the
results to the Darwin Core standard.

## Status

This project is an early-stage skeleton. The current codebase includes:

* configuration loading with default values in `config/config.default.toml`
* a Typer-based CLI with a stub `process` command
* minimal I/O helpers that compute image hashes and write CSV, JSONL, and a
  manifest file

OCR engines, quality-control heuristics, and full Darwin Core mapping are not yet
implemented.

## CLI Usage

Process a directory of images by invoking the CLI with Python:

```bash
python cli.py process --input /path/to/images --output /path/to/output [--config path/to/config.toml]
```

**Options**

* `--input` / `-i`: directory of JPG/PNG images to process
* `--output` / `-o`: directory where CSV, JSONL, and manifest files are written
* `--config` / `-c`: optional TOML file overriding the default configuration

The current implementation iterates images, computes SHA-256 hashes, and writes
placeholder outputs. OCR and data extraction will be added in future commits.

## Development

Install dependencies and run tests:

```bash
pip install -e .
pytest -q
```

Additional OCR engines (Apple Vision, Tesseract, GPT), quality-control checks,
and Darwin Core mapping logic will be implemented as the project evolves.

## Engine plugins

OCR and transformation engines are discovered at runtime.  Each engine module
registers the tasks it implements using:

```python
from engines import register_task
register_task("image_to_text", "my_engine", __name__, "image_to_text")
```

Engine implementations should follow the call signatures defined in ``engines.protocols``.
For OCR tasks implement :class:`engines.protocols.ImageToTextEngine` and for text extraction to Darwin
Core implement :class:`engines.protocols.TextToDwcEngine`.

Third-party packages can expose engines via Python entry points in their
`pyproject.toml`:

```toml
[project.entry-points."herbarium.engines"]
my_engine = "my_package.my_module"
```

The referenced module should call :func:`register_task` during import.


