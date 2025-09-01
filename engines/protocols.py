"""Protocol definitions for engine call signatures.

Third-party engines should implement these protocols so they can be
registered and dispatched correctly by the :mod:`engines` plugin system.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Protocol, Tuple


class ImageToTextEngine(Protocol):
    """Callable converting an image into text with token confidences."""

    def __call__(self, image: Path, *args, **kwargs) -> Tuple[str, List[float]]:
        """Extract text from ``image`` and return tokens and confidences."""
        ...


class TextToDwcEngine(Protocol):
    """Callable mapping unstructured text to Darwin Core terms."""

    def __call__(self, text: str, *args, **kwargs) -> Tuple[Dict[str, str], Dict[str, float]]:
        """Return Darwin Core data and per-field confidences."""
        ...


class ImageToDwcEngine(Protocol):
    """Callable mapping an image directly to Darwin Core terms."""

    def __call__(self, image: Path, *args, **kwargs) -> Tuple[Dict[str, str], Dict[str, float]]:
        """Return Darwin Core data and per-field confidences."""
        ...


__all__ = ["ImageToTextEngine", "TextToDwcEngine", "ImageToDwcEngine"]
