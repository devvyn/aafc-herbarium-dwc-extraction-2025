from __future__ import annotations


from pathlib import Path
from typing import List, Optional, Tuple

from .run import run
from .. import register_task
from ..protocols import ImageToTextEngine


def image_to_text(image: Path, langs: Optional[List[str]] = None) -> Tuple[str, List[float]]:
    """Extract text from an image using Apple's Vision framework.

    Parameters
    ----------
    image:
        Path to the image file.
    langs: list[str] | None
        Language hints. When ``None`` the framework performs automatic
        detection.

    Returns
    -------
    tuple
        A tuple containing the concatenated text and a list of token
        confidences.
    """

    tokens, _boxes, confidences = run(str(image), langs)
    text = " ".join(tokens)
    return text, confidences


register_task("image_to_text", "vision", __name__, "image_to_text")

# Static type checking helper
_IMAGE_TO_TEXT_CHECK: ImageToTextEngine = image_to_text

__all__ = ["image_to_text", "run"]
