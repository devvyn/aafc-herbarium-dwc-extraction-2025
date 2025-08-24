from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Dict, Any

import numpy as np
from PIL import Image, ImageOps


def grayscale(image: Image.Image) -> Image.Image:
    """Convert image to grayscale."""
    return ImageOps.grayscale(image)


def _principal_angle(gray: np.ndarray) -> float:
    coords = np.column_stack(np.where(gray < 255))
    if coords.size == 0:
        return 0.0
    y = coords[:, 0]
    x = coords[:, 1]
    cov = np.cov(x, y)
    eigvals, eigvecs = np.linalg.eig(cov)
    principal = eigvecs[:, np.argmax(eigvals)]
    angle = np.degrees(np.arctan2(principal[1], principal[0]))
    return angle


def deskew(image: Image.Image) -> Image.Image:
    """Attempt to deskew the image using its principal components."""
    gray = np.array(image.convert("L"))
    angle = _principal_angle(gray)
    return image.rotate(angle, expand=True, fillcolor=255)


def _otsu_threshold(gray: np.ndarray) -> int:
    hist, _ = np.histogram(gray.flatten(), bins=256, range=(0, 255))
    total = gray.size
    sum_total = np.dot(hist, np.arange(256))
    sumB = 0.0
    wB = 0.0
    max_var = 0.0
    threshold = 0
    for i in range(256):
        wB += hist[i]
        if wB == 0:
            continue
        wF = total - wB
        if wF == 0:
            break
        sumB += i * hist[i]
        mB = sumB / wB
        mF = (sum_total - sumB) / wF
        var_between = wB * wF * (mB - mF) ** 2
        if var_between > max_var:
            max_var = var_between
            threshold = i
    return threshold


def binarize(image: Image.Image, method: str | bool = "otsu") -> Image.Image:
    """Binarize an image using Otsu's threshold."""
    gray = np.array(image.convert("L"))
    thresh = _otsu_threshold(gray)
    binary = (gray > thresh).astype(np.uint8) * 255
    return Image.fromarray(binary)


def resize(image: Image.Image, max_dim: int) -> Image.Image:
    """Resize image so that its longest dimension equals ``max_dim``."""
    w, h = image.size
    max_current = max(w, h)
    if max_current <= max_dim:
        return image
    scale = max_dim / float(max_current)
    new_size = (int(w * scale), int(h * scale))
    return image.resize(new_size, Image.LANCZOS)


def preprocess_image(path: Path, cfg: Dict[str, Any]) -> Path:
    """Apply configured preprocessing steps to the image and return new path."""
    img = Image.open(path)
    if cfg.get("grayscale"):
        img = grayscale(img)
    if cfg.get("deskew"):
        img = deskew(img)
    binarize_method = cfg.get("binarize")
    if binarize_method:
        img = binarize(img)
    max_dim = cfg.get("max_dim_px")
    if max_dim:
        img = resize(img, int(max_dim))
    tmp = tempfile.NamedTemporaryFile(suffix=path.suffix or ".png", delete=False)
    img.save(tmp.name)
    return Path(tmp.name)


__all__ = [
    "grayscale",
    "deskew",
    "binarize",
    "resize",
    "preprocess_image",
]
