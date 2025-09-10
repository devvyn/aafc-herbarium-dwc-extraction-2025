"""Prototype preprocessing flows for different OCR engines."""

from __future__ import annotations

from typing import Dict, Any

# Recommended preprocessing configurations per engine. These dictionaries can
# be merged into a configuration file's ``[preprocess]`` section.

APPLE_VISION: Dict[str, Any] = {
    "pipeline": ["resize"],
    # Apple Vision handles color and skew internally. Limiting size keeps
    # memory usage reasonable. Values between 2500 and 3500 work well.
    "max_dim_px": 3072,
}

TESSERACT: Dict[str, Any] = {
    # Tesseract benefits from aggressive normalization and binarization.
    "pipeline": ["grayscale", "contrast", "deskew", "binarize", "resize"],
    "binarize_method": "adaptive",
    # Contrast factor of 1.3–1.7 sharpens faint text without clipping.
    "contrast_factor": 1.5,
    # Resize so the longest edge is around 3000–4000 pixels.
    "max_dim_px": 4000,
}

CHATGPT: Dict[str, Any] = {
    # GPT models operate on lower resolutions but benefit from some cleanup.
    "pipeline": ["grayscale", "contrast", "resize"],
    # Slight contrast boost helps legibility; avoid over-enhancement.
    "contrast_factor": 1.3,
    # Restrict size to keep prompts small. 1500–2500 pixels works well.
    "max_dim_px": 2048,
}

PADDLEOCR: Dict[str, Any] = {
    # PaddleOCR benefits from clean binaries at moderate resolution.
    "pipeline": ["grayscale", "binarize", "resize"],
    "binarize_method": "adaptive",
    # Resize so the longest edge is around 3000–4000 pixels.
    "max_dim_px": 4000,
}

__all__ = ["APPLE_VISION", "TESSERACT", "CHATGPT", "PADDLEOCR"]
