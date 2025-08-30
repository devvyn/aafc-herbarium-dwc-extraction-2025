# Herbarium OCR to Darwin Core

Toolkit for extracting text from herbarium specimen images and mapping the
results to the Darwin Core standard.

## Status

This project is an early-stage skeleton. The current codebase includes:

* configuration loading with default values in `config/config.default.toml`
* a Typer-based CLI with a stub `process` command
* minimal I/O helpers that compute image hashes and write CSV, JSONL, and a
  manifest file
* archive utilities that generate `meta.xml` and optionally zip outputs into a Darwin Core Archive bundle

Optional OCR engine plugins for Apple Vision, Tesseract, and GPT are available
and register themselves when their dependencies are installed.

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

The repository ships optional plugins for Apple Vision, Tesseract, and GPT
engines. Quality-control checks and full Darwin Core mapping logic will be
implemented as the project evolves.

## Preprocessing pipeline

Images can be passed through an ordered preprocessing pipeline before OCR.
Steps are referenced by name and resolved via a simple registry. Configure the
pipeline and step options in the `[preprocess]` section of the TOML file:

```toml
[preprocess]
pipeline = ["grayscale", "deskew", "binarize", "resize"]
max_dim_px = 4000  # used by the "resize" step
```

Built-in steps register themselves when `preprocess` is imported, and external
modules may register additional steps with
`preprocess.register_preprocessor(name, func)`.

## Engine plugins

Built-in plugins for Apple Vision (`vision`), Tesseract (`tesseract`), and GPT
(`gpt`) register themselves when their optional dependencies are installed.
Enable or restrict engines via the `[ocr]` section of your configuration:

```toml
[ocr]
enabled_engines = ["vision", "tesseract", "gpt"]
preferred_engine = "vision"
```

OCR and transformation engines are discovered at runtime.  Each engine module
registers the tasks it implements using:

```python
from engines import register_task
register_task("image_to_text", "my_engine", __name__, "image_to_text")
```

The registry loads these built-in plugins on import and discovers any
additional engines that advertise the `herbarium.engines` entry-point group.
Engine implementations should follow the call signatures defined in
``engines.protocols``. For OCR tasks implement
:class:`engines.protocols.ImageToTextEngine` and for text extraction to Darwin
Core implement :class:`engines.protocols.TextToDwcEngine`.

Third-party packages can expose engines via Python entry points in their
`pyproject.toml`:

```toml
[project.entry-points."herbarium.engines"]
my_engine = "my_package.my_module"
```

The referenced module should call :func:`register_task` during import.


