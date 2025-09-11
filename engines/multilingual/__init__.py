"""PaddleOCR-based multilingual OCR engine."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from .. import register_task
from ..errors import EngineError
from ..protocols import ImageToTextEngine


def image_to_text(
    image: Path,
    langs: List[str],
    model_paths: Dict[str, str] | None = None,
) -> Tuple[str, List[float]]:
    """Run PaddleOCR sequentially across multiple languages.

    Parameters
    ----------
    image:
        Path to the source image.
    langs:
        Languages to try in order.
    model_paths:
        Optional mapping of language codes to custom model directories.
    """

    try:  # pragma: no cover - optional dependency
        from paddleocr import PaddleOCR
    except Exception as exc:  # pragma: no cover - optional dependency
        raise EngineError("MISSING_DEPENDENCY", "paddleocr not available") from exc

    last_exc: Exception | None = None
    for lang in langs:
        kwargs = {"lang": lang, "use_angle_cls": True}
        if model_paths and lang in model_paths:
            kwargs["ocr_model_dir"] = model_paths[lang]
        try:  # pragma: no cover - runtime failure
            ocr = PaddleOCR(**kwargs)
            result = ocr.ocr(str(image), cls=True)
        except Exception as exc:  # pragma: no cover - runtime failure
            last_exc = exc
            continue

        tokens: List[str] = []
        confidences: List[float] = []
        for line in result:
            for _box, (text, conf) in line:
                tokens.append(text)
                confidences.append(float(conf))
        if tokens:
            return " ".join(tokens), confidences

    if last_exc is not None:
        raise EngineError("OCR_ERROR", str(last_exc)) from last_exc
    raise EngineError("OCR_ERROR", "no text extracted")


register_task("image_to_text", "multilingual", __name__, "image_to_text")

# Static type checking helper
_IMAGE_TO_TEXT_CHECK: ImageToTextEngine = image_to_text

__all__ = ["image_to_text"]
