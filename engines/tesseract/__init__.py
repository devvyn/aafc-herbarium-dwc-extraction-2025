from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from .. import register_task


def image_to_text(image: Path, oem: int, psm: int, langs: List[str], extra_args: List[str]) -> Tuple[str, float]:
    """Run Tesseract OCR on an image and return text and average confidence.

    Parameters
    ----------
    image: Path
        Path to the image file to OCR.
    oem: int
        OCR Engine Mode passed to Tesseract (``--oem``).
    psm: int
        Page Segmentation Mode passed to Tesseract (``--psm``).
    langs: list[str]
        Languages to use, joined with ``+`` for Tesseract's ``lang`` argument.
    extra_args: list[str]
        Additional command-line arguments passed to Tesseract.
    """
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
        float(c) for t, c in zip(data.get("text", []), data.get("conf", [])) if t.strip() and str(c) != "-1"
    ]
    text = " ".join(tokens)
    avg_conf = sum(confidences) / len(confidences) / 100 if confidences else 0.0
    return text, avg_conf

register_task("image_to_text", "tesseract", __name__, "image_to_text")

__all__ = ["image_to_text"]
