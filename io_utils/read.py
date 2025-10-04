from pathlib import Path
from typing import Iterable, Iterator, TYPE_CHECKING
import hashlib

if TYPE_CHECKING:
    from src.io_utils.locator import ImageLocator

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def _normalize_extensions(extensions: Iterable[str]) -> set[str]:
    return {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions}


def iter_images(input_dir: Path, extensions: Iterable[str] | None = None) -> Iterator[Path]:
    """Yield image paths from a directory recursively.

    Legacy function for local filesystem access. For storage abstraction,
    use iter_images_from_locator() instead.

    Args:
        input_dir: Directory containing images
        extensions: Optional set of file extensions to include

    Yields:
        Path objects for image files
    """
    allowed = _normalize_extensions(extensions) if extensions is not None else IMAGE_EXTENSIONS
    for path in sorted(input_dir.rglob("*")):
        if path.suffix.lower() in allowed:
            yield path


def iter_images_from_locator(locator: "ImageLocator", prefix: str | None = None) -> Iterator[str]:
    """Yield image identifiers from an ImageLocator.

    Storage-agnostic alternative to iter_images() that works with any
    ImageLocator backend (local, S3, MinIO, HTTP, etc.).

    Args:
        locator: ImageLocator instance
        prefix: Optional prefix filter (e.g., subdirectory, S3 prefix)

    Yields:
        Image identifiers (relative paths, S3 keys, URLs, etc.)

    Example:
        from src.io_utils.locator_factory import create_image_locator

        locator = create_image_locator(config)
        for identifier in iter_images_from_locator(locator):
            image_data = locator.get_image(identifier)
            # Process image...
    """
    yield from locator.list_images(prefix)


def compute_sha256(path: Path) -> str:
    """Compute the SHA256 hash of a file.

    Args:
        path: Path to file

    Returns:
        Hex string of SHA256 hash
    """
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_sha256_from_data(data: bytes) -> str:
    """Compute the SHA256 hash of binary data.

    Storage-agnostic alternative to compute_sha256() for use with
    ImageLocator.get_image() that returns bytes.

    Args:
        data: Raw binary data

    Returns:
        Hex string of SHA256 hash

    Example:
        locator = create_image_locator(config)
        image_data = locator.get_image("specimen_001.jpg")
        sha256 = compute_sha256_from_data(image_data)
    """
    return hashlib.sha256(data).hexdigest()
