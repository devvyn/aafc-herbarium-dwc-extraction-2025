# Multilingual OCR engine

The [`engines.multilingual`](../engines/multilingual/__init__.py) module wraps [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) to extract text from images in multiple languages. It is part of the OCR phase of the digitization pipeline and produces raw text and token confidences for downstream mapping.

## Installation

```bash
pip install paddlepaddle paddleocr
```

## Usage

```python
from pathlib import Path
from engines import dispatch
import engines.multilingual  # noqa: F401 ensures engine registration

text, confidences = dispatch(
    "image_to_text",
    image=Path("specimen.jpg"),
    engine="multilingual",
    langs=["fr", "en"],
)
```

The engine accepts ISO 639-1 (two-letter) and ISO 639-2 (three-letter) codes. Mixed lists such as `"eng"`, `"fr"`, and `"la"` are normalized automatically before invoking PaddleOCR, so the same configuration can drive Tesseract and multilingual OCR without manual edits.

## Supported languages

PaddleOCR's multilingual model covers 80+ languages including `en`, `fr`, `de`, `es`, `ru`, and `it`. Refer to the [PaddleOCR documentation](https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.7/doc/doc_en/models_list_en.md#multi-language-ocr-model-list) for the full list.
