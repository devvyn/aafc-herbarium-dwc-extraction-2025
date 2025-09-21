from pathlib import Path
from typing import Iterable, Iterator
import hashlib

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def _normalize_extensions(extensions: Iterable[str]) -> set[str]:
    return {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions}


def iter_images(input_dir: Path, extensions: Iterable[str] | None = None) -> Iterator[Path]:
    """Yield image paths from a directory recursively."""

    allowed = _normalize_extensions(extensions) if extensions is not None else IMAGE_EXTENSIONS
    for path in sorted(input_dir.rglob("*")):
        if path.suffix.lower() in allowed:
            yield path


def compute_sha256(path: Path) -> str:
    """Compute the SHA256 hash of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
