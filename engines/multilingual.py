"""Multilingual OCR engine using PaddleOCR models."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from . import register_task
from .errors import EngineError
from .protocols import ImageToTextEngine


def image_to_text(image: Path, langs: List[str]) -> Tuple[str, List[float]]:
    """Extract text from ``image`` using PaddleOCR for each language."""

    try:  # pragma: no cover - optional dependency
        from paddleocr import PaddleOCR
    except Exception as exc:  # pragma: no cover - optional dependency
        raise EngineError("MISSING_DEPENDENCY", "paddleocr not available") from exc

    languages = langs or ["en"]
    tokens: List[str] = []
    confidences: List[float] = []

    for lang in languages:
        try:  # pragma: no cover - runtime failure
            ocr = PaddleOCR(lang=lang, use_angle_cls=True)
            result = ocr.ocr(str(image), cls=True)
        except Exception as exc:  # pragma: no cover - runtime failure
            raise EngineError("OCR_ERROR", str(exc)) from exc

        for line in result:
            for _box, (text, conf) in line:
                tokens.append(text)
                confidences.append(float(conf))

    text = " ".join(tokens)
    return text, confidences


register_task("image_to_text", "multilingual", __name__, "image_to_text")

# Static type checking helper
_IMAGE_TO_TEXT_CHECK: ImageToTextEngine = image_to_text

__all__ = ["image_to_text"]

