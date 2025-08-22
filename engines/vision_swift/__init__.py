"""Interface to Apple's Vision text recognition via Swift."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from .run import run


def image_to_text(image: Path) -> Tuple[str, List[float]]:
    """Extract text from an image using Apple's Vision framework.

    Parameters
    ----------
    image:
        Path to the image file.

    Returns
    -------
    tuple
        A tuple containing the concatenated text and a list of token
        confidences.
    """

    tokens, _boxes, confidences = run(str(image))
    text = " ".join(tokens)
    return text, confidences


__all__ = ["image_to_text", "run"]
