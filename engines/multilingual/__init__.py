"""Stub module for multilingual OCR engine.

This stub establishes a placeholder for integrating multilingual OCR models
(see issue #138). The implementation will load language-specific models and
expose a unified :func:`image_to_text` API matching other OCR engines.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from .. import register_task
from ..protocols import ImageToTextEngine


def image_to_text(
    image: Path,
    langs: List[str],
    model_paths: Dict[str, str] | None = None,
) -> Tuple[str, List[float]]:
    """Placeholder for multilingual OCR extraction.

    Parameters
    ----------
    image:
        Path to the source image.
    langs:
        Language codes to apply during recognition.
    model_paths:
        Optional mapping of language codes to custom model paths.
    """

    raise NotImplementedError("Multilingual OCR engine is not yet implemented")


register_task("image_to_text", "multilingual", __name__, "image_to_text")

# Static type checking helper
_IMAGE_TO_TEXT_CHECK: ImageToTextEngine = image_to_text

__all__ = ["image_to_text"]
