# Multilingual OCR engine

The multilingual OCR engine builds on [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
and tries each requested language until text is extracted. Use it when labels
include multiple scripts or non-English text.

## Installation

```bash
uv add ".[paddleocr]"
# or
pip install paddleocr paddlepaddle
```

## Usage

```python
from pathlib import Path
from engines import dispatch

text, conf = dispatch(
    "image_to_text",
    image=Path("specimen.jpg"),
    engine="multilingual",
    langs=["fr", "en"],
)
print(text)
```

## Supported languages

PaddleOCR ships models for more than 80 languages including Arabic, Chinese,
English, French, German, Japanese, Korean, Russian and Spanish. See the
[PaddleOCR language guide](https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.7/doc/doc_en/multi_languages.md)
for the full list and additional setup notes.
