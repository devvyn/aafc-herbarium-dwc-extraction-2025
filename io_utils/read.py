from pathlib import Path
from typing import Iterator
import hashlib

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

def iter_images(input_dir: Path) -> Iterator[Path]:
    """Yield image paths from a directory recursively."""
    for path in sorted(input_dir.rglob("*")):
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            yield path

def compute_sha256(path: Path) -> str:
    """Compute the SHA256 hash of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
