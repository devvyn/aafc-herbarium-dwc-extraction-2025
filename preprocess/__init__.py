from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Dict, Any, Callable

import numpy as np
from PIL import Image, ImageOps, ImageEnhance

_PREPROCESSORS: Dict[str, Callable[[Image.Image, Dict[str, Any]], Image.Image]] = {}


def register_preprocessor(
    name: str, func: Callable[[Image.Image, Dict[str, Any]], Image.Image]
) -> None:
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


def _sauvola_threshold(
    gray: np.ndarray, window_size: int = 25, k: float = 0.2, r: int = 128
) -> np.ndarray:
    """Compute Sauvola threshold surface for ``gray`` image."""
    pad = window_size // 2
    padded = np.pad(gray, pad, mode="reflect")
    integral = np.cumsum(np.cumsum(padded, axis=0), axis=1)
    integral = np.pad(integral, ((1, 0), (1, 0)), mode="constant")
    integral_sq = np.cumsum(np.cumsum(padded**2, axis=0), axis=1)
    integral_sq = np.pad(integral_sq, ((1, 0), (1, 0)), mode="constant")
    w = window_size
    sum_ = integral[w:, w:] - integral[:-w, w:] - integral[w:, :-w] + integral[:-w, :-w]
    sum_sq = (
        integral_sq[w:, w:] - integral_sq[:-w, w:] - integral_sq[w:, :-w] + integral_sq[:-w, :-w]
    )
    area = w * w
    mean = sum_ / area
    variance = sum_sq / area - mean**2
    std = np.sqrt(np.maximum(variance, 0))
    return mean * (1 + k * (std / r - 1))


def adaptive_threshold(image: Image.Image, window_size: int = 25, k: float = 0.2) -> Image.Image:
    """Binarize an image using Sauvola's adaptive threshold."""
    gray = np.array(image.convert("L"), dtype=float)
    h, w = gray.shape
    window_size = min(window_size, h, w)
    if window_size % 2 == 0:
        window_size -= 1
    window_size = max(window_size, 3)
    thresh = _sauvola_threshold(gray, window_size=window_size, k=k)
    binary = (gray > thresh).astype(np.uint8) * 255
    return Image.fromarray(binary)


def binarize(image: Image.Image, method: str | bool = "otsu", **kwargs) -> Image.Image:
    """Binarize ``image`` using the chosen ``method``."""
    method_str = str(method).lower() if not isinstance(method, bool) else "otsu"
    if method_str == "adaptive":
        raw_window = kwargs.get("window_size")
        raw_k = kwargs.get("k")
        window = int(raw_window) if raw_window is not None else 25
        k = float(raw_k) if raw_k is not None else 0.2
        return adaptive_threshold(image, window, k)
    gray = np.array(image.convert("L"))
    thresh = _otsu_threshold(gray)
    binary = (gray > thresh).astype(np.uint8) * 255
    return Image.fromarray(binary)


def contrast(image: Image.Image, factor: float) -> Image.Image:
    """Adjust image contrast by ``factor``."""
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)


def resize(image: Image.Image, max_dim: int) -> Image.Image:
    """Resize image so that its longest dimension equals ``max_dim``."""
    w, h = image.size
    max_current = max(w, h)
    if max_current <= max_dim:
        return image
    scale = max_dim / float(max_current)
    new_size = (int(w * scale), int(h * scale))
    return image.resize(new_size, Image.Resampling.LANCZOS)


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
register_preprocessor(
    "binarize",
    lambda img, cfg: binarize(
        img,
        cfg.get("binarize_method", "otsu"),
        window_size=cfg.get("adaptive_window_size"),
        k=cfg.get("adaptive_k"),
    ),
)
register_preprocessor(
    "adaptive_threshold",
    lambda img, cfg: adaptive_threshold(
        img,
        int(cfg.get("adaptive_window_size", 25)),
        float(cfg.get("adaptive_k", 0.2)),
    ),
)


def _contrast_step(img: Image.Image, cfg: Dict[str, Any]) -> Image.Image:
    factor = cfg.get("contrast_factor")
    if factor:
        return contrast(img, float(factor))
    return img


register_preprocessor("contrast", _contrast_step)


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
    "adaptive_threshold",
    "contrast",
    "resize",
    "preprocess_image",
]
