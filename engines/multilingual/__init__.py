"""PaddleOCR-backed multilingual OCR engine.

This module wraps the :mod:`paddleocr` package to provide text extraction for
multiple languages.  It iterates over the requested language codes and returns
the first successful recognition result.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from .. import register_task
from ..errors import EngineError
from ..protocols import ImageToTextEngine
from ..language_codes import normalize_iso2


def image_to_text(
    image: Path,
    langs: List[str],
    model_paths: Dict[str, str] | None = None,
) -> Tuple[str, List[float]]:
    """Extract multilingual text from ``image``.

    Parameters
    ----------
    image:
        Path to the source image.
    langs:
        Language codes to try in priority order.
    model_paths:
        Optional mapping of language codes to custom model paths.  Currently
        unused, reserved for future customization.
    """

    try:  # pragma: no cover - optional dependency
        from paddleocr import PaddleOCR
    except Exception as exc:  # pragma: no cover - optional dependency
        raise EngineError("MISSING_DEPENDENCY", "paddleocr not available") from exc

    tokens: List[str] = []
    confidences: List[float] = []
    if langs:
        try:
            languages = normalize_iso2(langs)
        except ValueError as exc:
            raise EngineError("INVALID_LANGUAGE", str(exc)) from exc
    else:
        languages = ["en"]
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
        if tokens:
            break

    text = " ".join(tokens)
    return text, confidences


register_task("image_to_text", "multilingual", __name__, "image_to_text")

# Static type checking helper
_IMAGE_TO_TEXT_CHECK: ImageToTextEngine = image_to_text

__all__ = ["image_to_text"]
