from __future__ import annotations


from pathlib import Path
from typing import List, Tuple

from .. import register_task
from ..protocols import ImageToTextEngine


def image_to_text(image: Path, oem: int, psm: int, langs: List[str], extra_args: List[str]) -> Tuple[str, List[float]]:
    """Run Tesseract OCR on an image and return text and token confidences."""
    import pytesseract
    from pytesseract import Output

    config_parts = [f"--oem {oem}", f"--psm {psm}"]
    if extra_args:
        config_parts.extend(extra_args)
    config = " ".join(config_parts)
    lang = "+".join(langs)

    data = pytesseract.image_to_data(
        str(image), lang=lang, config=config, output_type=Output.DICT
    )
    tokens = [t for t in data.get("text", []) if t.strip()]
    confidences = [
        float(c) / 100
        for t, c in zip(data.get("text", []), data.get("conf", []))
        if t.strip() and str(c) != "-1"
    ]
    text = " ".join(tokens)
    return text, confidences


register_task("image_to_text", "tesseract", __name__, "image_to_text")

# Static type checking helper
_IMAGE_TO_TEXT_CHECK: ImageToTextEngine = image_to_text

__all__ = ["image_to_text"]
