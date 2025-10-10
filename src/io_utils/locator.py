"""Image location abstraction layer.

This module defines the core ImageLocator protocol that decouples the extraction
pipeline from storage implementation details. Storage backends (S3, MinIO, local
filesystem, HTTP) implement this interface.

Architecture:
- Core extraction logic operates on ImageLocator, not Path objects
- Transparent pass-through caching via decorator pattern
- Pluggable backends selected at runtime via configuration
- No changes to extraction logic when switching storage backends

Example:
    # Core code uses abstract interface
    locator = get_image_locator(config)  # Returns S3, local, or MinIO
    image_data = locator.get_image("specimen_123.jpg")

    # With transparent caching (core code unchanged)
    locator = CachingImageLocator(S3ImageLocator(bucket="my-bucket"))
    image_data = locator.get_image("specimen_123.jpg")  # Cached automatically
"""

from pathlib import Path
from typing import Protocol, Iterator, Optional
from dataclasses import dataclass


@dataclass
class ImageMetadata:
    """Metadata about an image.

    Attributes:
        identifier: Unique identifier for the image (filename, S3 key, URL)
        size_bytes: Size of the image in bytes (None if unknown)
        last_modified: Last modification timestamp (None if unknown)
        content_type: MIME type (e.g., "image/jpeg")
        source_uri: Original URI/path where image is stored
    """

    identifier: str
    size_bytes: Optional[int] = None
    last_modified: Optional[float] = None
    content_type: Optional[str] = None
    source_uri: Optional[str] = None


class ImageLocator(Protocol):
    """Protocol defining the interface for image storage backends.

    This protocol abstracts away storage implementation details, allowing the
    core extraction pipeline to work with images regardless of whether they're
    stored in S3, MinIO, local filesystem, or fetched via HTTP.

    All methods should be idempotent and thread-safe where possible.
    """

    def exists(self, identifier: str) -> bool:
        """Check if an image exists.

        Args:
            identifier: Image identifier (filename, S3 key, URL, etc.)

        Returns:
            True if image exists and is accessible, False otherwise
        """
        ...

    def get_image(self, identifier: str) -> bytes:
        """Retrieve image data.

        Args:
            identifier: Image identifier (filename, S3 key, URL, etc.)

        Returns:
            Raw image bytes

        Raises:
            FileNotFoundError: Image does not exist
            PermissionError: Image exists but cannot be accessed
            IOError: Network error, read failure, etc.
        """
        ...

    def get_metadata(self, identifier: str) -> ImageMetadata:
        """Get metadata about an image.

        Args:
            identifier: Image identifier (filename, S3 key, URL, etc.)

        Returns:
            ImageMetadata object with available information

        Raises:
            FileNotFoundError: Image does not exist
        """
        ...

    def list_images(self, prefix: Optional[str] = None) -> Iterator[str]:
        """List available images.

        Args:
            prefix: Optional prefix filter (e.g., directory path, S3 prefix)

        Yields:
            Image identifiers matching the prefix

        Note:
            For large datasets, this should be implemented as a generator
            to avoid loading all identifiers into memory.
        """
        ...

    def get_local_path(self, identifier: str) -> Optional[Path]:
        """Get local filesystem path for an image, if available.

        This is an optimization for backends that store images locally.
        For remote backends (S3, HTTP), this may return None, triggering
        automatic download/caching behavior in the caller.

        Args:
            identifier: Image identifier (filename, S3 key, URL, etc.)

        Returns:
            Path object if image is available locally, None otherwise

        Note:
            Returning None does not mean the image doesn't exist - it means
            the image must be fetched via get_image() instead of direct
            filesystem access.
        """
        ...
