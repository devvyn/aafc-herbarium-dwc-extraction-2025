# Multilingual OCR engine

The [multilingual OCR engine](../engines/multilingual/__init__.py) wraps
PaddleOCR's language models to recognize non-English labels during the
preprocessing phase. Extracted text and confidences are stored in the pipeline's
SQLite database, keeping raw OCR output separate from the main DwC+ABCD store.

## Installation

Install PaddleOCR to enable the engine:

```sh
pip install paddleocr
```

The models download on first use and are cached under the user's home
directory. No data are written to the central database until an explicit import
step.

## Usage

Run the engine from Python using the task dispatcher:

```python
from pathlib import Path
from engines import dispatch

text, conf = dispatch(
    "image_to_text",
    image=Path("label.jpg"),
    engine="multilingual",
    langs=["fr", "en"],
)
```

This example sequentially applies French and English models and aggregates the
results. The command-line interfaces under `./scripts` provide equivalent
workflow steps.

## Supported languages

PaddleOCR ships recognition models for over 80 languages including `ar`, `en`,
`fr`, `de`, `es`, `ru`, `zh`, and more. Consult the
[PaddleOCR language table](https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.7/doc/doc_en/multi_languages.md)
for the full list.

