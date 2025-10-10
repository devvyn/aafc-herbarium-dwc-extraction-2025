"""Local filesystem storage backend."""

import mimetypes
from pathlib import Path
from typing import Iterator, Optional

from ..locator import ImageMetadata


class LocalFilesystemLocator:
    """ImageLocator implementation for local filesystem storage.

    This is the simplest backend - images are stored on the local filesystem
    and accessed directly via Path objects. No caching needed since files are
    already local.

    Args:
        base_path: Root directory containing images

    Example:
        locator = LocalFilesystemLocator(Path("/data/images"))
        image_data = locator.get_image("specimen_001.jpg")
        # Reads from /data/images/specimen_001.jpg
    """

    def __init__(self, base_path: Path):
        """Initialize local filesystem locator.

        Args:
            base_path: Root directory containing images

        Raises:
            ValueError: base_path is not a directory
        """
        self.base_path = Path(base_path)
        if not self.base_path.is_dir():
            raise ValueError(f"Base path is not a directory: {base_path}")

    def exists(self, identifier: str) -> bool:
        """Check if an image exists.

        Args:
            identifier: Relative path from base_path (e.g., "subdir/image.jpg")

        Returns:
            True if image file exists and is readable
        """
        path = self.base_path / identifier
        return path.is_file()

    def get_image(self, identifier: str) -> bytes:
        """Retrieve image data.

        Args:
            identifier: Relative path from base_path

        Returns:
            Raw image bytes

        Raises:
            FileNotFoundError: Image file does not exist
            PermissionError: Image file exists but cannot be read
        """
        path = self.base_path / identifier
        if not path.is_file():
            raise FileNotFoundError(f"Image not found: {identifier}")

        try:
            return path.read_bytes()
        except PermissionError:
            raise PermissionError(f"Cannot read image: {identifier}")

    def get_metadata(self, identifier: str) -> ImageMetadata:
        """Get metadata about an image.

        Args:
            identifier: Relative path from base_path

        Returns:
            ImageMetadata with file information

        Raises:
            FileNotFoundError: Image file does not exist
        """
        path = self.base_path / identifier
        if not path.is_file():
            raise FileNotFoundError(f"Image not found: {identifier}")

        stat = path.stat()
        content_type, _ = mimetypes.guess_type(str(path))

        return ImageMetadata(
            identifier=identifier,
            size_bytes=stat.st_size,
            last_modified=stat.st_mtime,
            content_type=content_type,
            source_uri=str(path),
        )

    def list_images(self, prefix: Optional[str] = None) -> Iterator[str]:
        """List available images.

        Args:
            prefix: Optional subdirectory prefix (e.g., "batch1/")

        Yields:
            Relative paths to image files (e.g., "batch1/image_001.jpg")

        Note:
            Only yields files with common image extensions:
            .jpg, .jpeg, .png, .tif, .tiff, .bmp, .gif
        """
        image_extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif"}

        search_path = self.base_path / prefix if prefix else self.base_path

        if not search_path.exists():
            return

        # Recursively find all image files
        for path in search_path.rglob("*"):
            if path.is_file() and path.suffix.lower() in image_extensions:
                # Return path relative to base_path
                relative_path = path.relative_to(self.base_path)
                yield str(relative_path)

    def get_local_path(self, identifier: str) -> Optional[Path]:
        """Get local filesystem path for an image.

        For LocalFilesystemLocator, this always returns the actual path
        since images are already on the local filesystem.

        Args:
            identifier: Relative path from base_path

        Returns:
            Absolute Path to the image file, or None if file doesn't exist
        """
        path = self.base_path / identifier
        return path if path.is_file() else None
