"""Multilingual OCR engine stubs."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from . import register_task


def image_to_text(image: Path, langs: List[str]) -> Tuple[str, List[float]]:
    """Extract text from an image using a multilingual OCR model.

    This is a placeholder for future multilingual OCR integration.
    See [Issue #138](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/138).
    """

    raise NotImplementedError("Multilingual OCR support is not yet implemented.")


register_task("image_to_text", "multilingual", __name__, "image_to_text")

__all__ = ["image_to_text"]
