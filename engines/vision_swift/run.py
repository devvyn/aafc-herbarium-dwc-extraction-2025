"""Python wrapper for the Swift Vision text recognition engine."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple


def run(
    image_path: str, langs: Optional[List[str]] = None
) -> Tuple[List[str], List[List[float]], List[float]]:
    """Run the Swift Vision text recognizer.

    Parameters
    ----------
    image_path: str
        Path to the image file to process.
    langs: list[str] | None
        Language hints passed to ``VNRecognizeTextRequest``. When ``None`` the
        framework attempts automatic language detection.

    Returns
    -------
    tuple
        Three lists: recognized text tokens, bounding boxes, and confidences.
    """

    pkg_dir = Path(__file__).resolve().parent
    cmd = [
        "swift",
        "run",
        "--package-path",
        str(pkg_dir),
        "vision_swift",
        image_path,
    ]
    if langs:
        cmd.extend(langs)

    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    results = json.loads(proc.stdout)

    tokens = [r["text"] for r in results]
    boxes = [r["boundingBox"] for r in results]
    confidences = [r["confidence"] for r in results]
    return tokens, boxes, confidences


__all__ = ["run"]
