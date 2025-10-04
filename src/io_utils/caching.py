"""Transparent pass-through caching for ImageLocator backends.

This module implements the decorator pattern to add caching to any ImageLocator
backend without the core extraction logic knowing about it.

Architecture Pattern:
- Decorator wraps any ImageLocator implementation
- Cache hit: Return from local filesystem (fast)
- Cache miss: Fetch from wrapped backend, save to cache, return
- Core extraction logic: Unchanged, uses ImageLocator interface

Example:
    # Without caching (S3 fetch on every access)
    locator = S3ImageLocator(bucket="my-bucket")
    image_data = locator.get_image("specimen_001.jpg")  # Slow S3 fetch

    # With transparent caching (core code unchanged)
    locator = CachingImageLocator(
        S3ImageLocator(bucket="my-bucket"),
        cache_dir=Path("/tmp/image-cache")
    )
    image_data = locator.get_image("specimen_001.jpg")  # Fast local cache
"""

import hashlib
import shutil
from pathlib import Path
from typing import Iterator, Optional

from .locator import ImageLocator, ImageMetadata


class CachingImageLocator:
    """Decorator that adds transparent pass-through caching to any ImageLocator.

    This class wraps another ImageLocator and caches fetched images on the local
    filesystem. The cache is transparent - callers use the same ImageLocator
    interface and don't need to know about caching.

    Cache Strategy:
    - Cache key: SHA256 hash of identifier (handles special chars, long names)
    - Cache hit: Return from local filesystem
    - Cache miss: Fetch from wrapped backend, save to cache, return
    - Metadata: Stored alongside image as {cache_key}.meta.json

    Args:
        backend: The wrapped ImageLocator backend (S3, HTTP, etc.)
        cache_dir: Local directory for cached images
        max_cache_size_mb: Optional maximum cache size in MB (None = unlimited)

    Example:
        # Wrap any backend with caching
        s3_backend = S3ImageLocator(bucket="my-bucket")
        cached_locator = CachingImageLocator(s3_backend, Path("/tmp/cache"))

        # First access: cache miss, fetches from S3
        data = cached_locator.get_image("specimen_001.jpg")

        # Second access: cache hit, returns from local filesystem
        data = cached_locator.get_image("specimen_001.jpg")  # Fast!
    """

    def __init__(
        self,
        backend: ImageLocator,
        cache_dir: Path,
        max_cache_size_mb: Optional[int] = None,
    ):
        """Initialize caching decorator.

        Args:
            backend: ImageLocator backend to wrap
            cache_dir: Directory for cached images
            max_cache_size_mb: Optional maximum cache size (None = unlimited)

        Raises:
            ValueError: cache_dir exists but is not a directory
        """
        self.backend = backend
        self.cache_dir = Path(cache_dir)
        self.max_cache_size_mb = max_cache_size_mb

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if not self.cache_dir.is_dir():
            raise ValueError(f"Cache path is not a directory: {cache_dir}")

    def _get_cache_key(self, identifier: str) -> str:
        """Generate cache key for an identifier.

        Uses SHA256 hash to handle:
        - Special characters in identifiers
        - Very long identifiers
        - S3 keys with slashes

        Args:
            identifier: Image identifier

        Returns:
            Hex string suitable for filename
        """
        return hashlib.sha256(identifier.encode()).hexdigest()

    def _get_cache_path(self, identifier: str) -> Path:
        """Get cache file path for an identifier.

        Args:
            identifier: Image identifier

        Returns:
            Path to cached image file
        """
        cache_key = self._get_cache_key(identifier)
        return self.cache_dir / cache_key

    def _is_cached(self, identifier: str) -> bool:
        """Check if image is in cache.

        Args:
            identifier: Image identifier

        Returns:
            True if image exists in cache
        """
        cache_path = self._get_cache_path(identifier)
        return cache_path.is_file()

    def _save_to_cache(self, identifier: str, data: bytes) -> None:
        """Save image data to cache.

        Args:
            identifier: Image identifier
            data: Raw image bytes
        """
        cache_path = self._get_cache_path(identifier)
        cache_path.write_bytes(data)

    def _load_from_cache(self, identifier: str) -> bytes:
        """Load image data from cache.

        Args:
            identifier: Image identifier

        Returns:
            Raw image bytes from cache

        Raises:
            FileNotFoundError: Image not in cache
        """
        cache_path = self._get_cache_path(identifier)
        if not cache_path.is_file():
            raise FileNotFoundError(f"Image not in cache: {identifier}")
        return cache_path.read_bytes()

    def _evict_cache_if_needed(self) -> None:
        """Evict oldest cache entries if cache exceeds max size.

        Uses LRU (Least Recently Used) eviction strategy based on file access time.
        """
        if self.max_cache_size_mb is None:
            return

        # Calculate total cache size
        total_size = sum(f.stat().st_size for f in self.cache_dir.iterdir() if f.is_file())
        max_size_bytes = self.max_cache_size_mb * 1024 * 1024

        if total_size <= max_size_bytes:
            return

        # Sort files by access time (oldest first)
        files = sorted(
            [f for f in self.cache_dir.iterdir() if f.is_file()],
            key=lambda f: f.stat().st_atime,
        )

        # Evict oldest files until under limit
        for file in files:
            if total_size <= max_size_bytes:
                break
            file_size = file.stat().st_size
            file.unlink()
            total_size -= file_size

    def exists(self, identifier: str) -> bool:
        """Check if an image exists.

        Checks cache first, then backend if not cached.

        Args:
            identifier: Image identifier

        Returns:
            True if image exists (cached or in backend)
        """
        if self._is_cached(identifier):
            return True
        return self.backend.exists(identifier)

    def get_image(self, identifier: str) -> bytes:
        """Retrieve image data with transparent caching.

        Cache hit: Return from local filesystem
        Cache miss: Fetch from backend, save to cache, return

        Args:
            identifier: Image identifier

        Returns:
            Raw image bytes

        Raises:
            FileNotFoundError: Image does not exist
            PermissionError: Image exists but cannot be accessed
            IOError: Network error, read failure, etc.
        """
        # Cache hit: return from local filesystem
        if self._is_cached(identifier):
            return self._load_from_cache(identifier)

        # Cache miss: fetch from backend
        data = self.backend.get_image(identifier)

        # Save to cache
        self._save_to_cache(identifier, data)

        # Evict old entries if cache too large
        self._evict_cache_if_needed()

        return data

    def get_metadata(self, identifier: str) -> ImageMetadata:
        """Get metadata about an image.

        Always fetches from backend (metadata is small, not worth caching).

        Args:
            identifier: Image identifier

        Returns:
            ImageMetadata object

        Raises:
            FileNotFoundError: Image does not exist
        """
        return self.backend.get_metadata(identifier)

    def list_images(self, prefix: Optional[str] = None) -> Iterator[str]:
        """List available images.

        Delegates to backend (cache doesn't track all available images).

        Args:
            prefix: Optional prefix filter

        Yields:
            Image identifiers from backend
        """
        yield from self.backend.list_images(prefix)

    def get_local_path(self, identifier: str) -> Optional[Path]:
        """Get local filesystem path for an image.

        Returns:
            - Cache path if image is cached
            - Backend path if backend provides local path
            - None if image must be fetched

        This optimization allows callers to use direct filesystem access
        when possible instead of loading entire image into memory.

        Args:
            identifier: Image identifier

        Returns:
            Path to local file, or None if must fetch via get_image()
        """
        # Check cache first
        if self._is_cached(identifier):
            return self._get_cache_path(identifier)

        # Check if backend provides local path
        backend_path = self.backend.get_local_path(identifier)
        if backend_path:
            return backend_path

        # Image must be fetched via get_image()
        return None

    def clear_cache(self) -> None:
        """Clear all cached images.

        Useful for testing or freeing disk space.
        """
        for file in self.cache_dir.iterdir():
            if file.is_file():
                file.unlink()

    def get_cache_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats:
            - num_files: Number of cached files
            - total_size_mb: Total cache size in MB
            - oldest_access: Timestamp of least recently accessed file
            - newest_access: Timestamp of most recently accessed file
        """
        files = [f for f in self.cache_dir.iterdir() if f.is_file()]

        if not files:
            return {
                "num_files": 0,
                "total_size_mb": 0.0,
                "oldest_access": None,
                "newest_access": None,
            }

        total_size = sum(f.stat().st_size for f in files)
        access_times = [f.stat().st_atime for f in files]

        return {
            "num_files": len(files),
            "total_size_mb": total_size / (1024 * 1024),
            "oldest_access": min(access_times),
            "newest_access": max(access_times),
        }
