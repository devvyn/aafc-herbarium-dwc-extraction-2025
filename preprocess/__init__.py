from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Dict, Any, Callable

import numpy as np
from PIL import Image, ImageOps

_PREPROCESSORS: Dict[str, Callable[[Image.Image, Dict[str, Any]], Image.Image]] = {}


def register_preprocessor(name: str, func: Callable[[Image.Image, Dict[str, Any]], Image.Image]) -> None:
    """Register a preprocessing step.

    Steps are called with the current :class:`PIL.Image.Image` and the
    ``preprocess`` section of the configuration and must return a new image.
    """
    _PREPROCESSORS[name] = func


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
    for step in cfg.get("pipeline", []):
        func = _PREPROCESSORS.get(step)
        if not func:
            raise KeyError(f"Preprocessor '{step}' is not registered")
        img = func(img, cfg)
    tmp = tempfile.NamedTemporaryFile(suffix=path.suffix or ".png", delete=False)
    img.save(tmp.name)
    return Path(tmp.name)


register_preprocessor("grayscale", lambda img, cfg: grayscale(img))
register_preprocessor("deskew", lambda img, cfg: deskew(img))
register_preprocessor("binarize", lambda img, cfg: binarize(img))


def _resize_step(img: Image.Image, cfg: Dict[str, Any]) -> Image.Image:
    max_dim = cfg.get("max_dim_px")
    if max_dim:
        return resize(img, int(max_dim))
    return img


register_preprocessor("resize", _resize_step)

__all__ = [
    "register_preprocessor",
    "grayscale",
    "deskew",
    "binarize",
    "resize",
    "preprocess_image",
]
