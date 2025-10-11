"""
Cached Image Source Wrapper

Integrates JIT caching and path registry with ImageSource abstraction
for robust, production-ready image access with automatic fallback.

Features:
- Transparent caching layer over any ImageSource
- Automatic path registry updates
- Graceful fallback on cache misses
- Event emission for monitoring
"""

import logging
import time
from pathlib import Path
from typing import Optional

from .image_source import ImageSource
from .jit_cache import JITImageCache
from .path_registry import ImagePathRegistry

logger = logging.getLogger(__name__)


class CachedImageSource:
    """
    Cached wrapper around ImageSource with path registry integration.

    Provides transparent caching with automatic fallback to source
    when cache entries are missing or expired.
    """

    def __init__(
        self,
        source: ImageSource,
        cache: JITImageCache,
        registry: Optional[ImagePathRegistry] = None,
        source_name: str = "default",
    ):
        """
        Initialize cached image source.

        Args:
            source: Underlying ImageSource (S3, local, multi)
            cache: JIT cache instance
            registry: Path registry instance (optional)
            source_name: Name for this source (for registry tracking)
        """
        self.source = source
        self.cache = cache
        self.registry = registry
        self.source_name = source_name

        logger.info(f"Cached source initialized: {source_name}")

    def get_image_path(self, sha256_hash: str, download: bool = True) -> Optional[Path]:
        """
        Get local path to image, downloading and caching if necessary.

        Args:
            sha256_hash: SHA256 hash of image
            download: Whether to download if not in cache

        Returns:
            Path to local cached file, or None if unavailable
        """
        start_time = time.time()

        # Step 1: Check cache
        cached_path = self.cache.get(sha256_hash)
        if cached_path:
            logger.debug(
                f"Cache hit: {sha256_hash[:16]}... ({(time.time() - start_time) * 1000:.1f}ms)"
            )
            return cached_path

        # Step 2: Check registry for known locations
        if self.registry:
            best_location = self.registry.get_best_location(sha256_hash)
            if best_location and best_location.location_type == "cache":
                # Try the registered cache location
                cached_path = Path(best_location.path)
                if cached_path.exists():
                    # Re-add to cache (may have expired from metadata)
                    self.cache.put(sha256_hash, cached_path, source=self.source_name)
                    logger.debug(f"Registry cache hit: {sha256_hash[:16]}...")
                    return cached_path

        # Step 3: Download from source if allowed
        if not download:
            logger.debug(f"Not in cache, download=False: {sha256_hash[:16]}...")
            return None

        logger.debug(f"Cache miss, downloading: {sha256_hash[:16]}...")

        # Create cache directory if needed
        cache_file = (
            self.cache.cache_dir
            / f"{sha256_hash[:2]}"
            / f"{sha256_hash[:4]}"
            / f"{sha256_hash}.jpg"
        )
        cache_file.parent.mkdir(parents=True, exist_ok=True)

        # Download from source
        try:
            success = self.source.download_image(sha256_hash, cache_file)

            if success and cache_file.exists():
                # Add to cache
                self.cache.put(sha256_hash, cache_file, source=self.source_name)

                # Register in path registry
                if self.registry:
                    # Register cache location
                    self.registry.register_location(
                        sha256_hash=sha256_hash,
                        location_type="cache",
                        path=str(cache_file),
                        size_bytes=cache_file.stat().st_size,
                        source_manifest=None,
                        verified=True,
                    )

                    # Also register source location (for future reference)
                    source_path = self.source.get_image_path(sha256_hash)
                    if source_path:
                        # Determine source type
                        source_type = (
                            "s3"
                            if source_path.startswith("s3://")
                            else "http"
                            if source_path.startswith("http")
                            else "local"
                        )

                        self.registry.register_location(
                            sha256_hash=sha256_hash,
                            location_type=source_type,
                            path=source_path,
                            source_manifest=None,
                            verified=True,
                        )

                self.cache.stats.downloads += 1
                elapsed_ms = (time.time() - start_time) * 1000
                logger.debug(
                    f"Downloaded and cached: {sha256_hash[:16]}... "
                    f"({cache_file.stat().st_size / 1024:.1f} KB, {elapsed_ms:.1f}ms)"
                )

                return cache_file

            else:
                logger.warning(f"Download failed: {sha256_hash[:16]}...")
                self.cache.stats.errors += 1
                return None

        except Exception as e:
            logger.error(f"Error downloading image {sha256_hash[:16]}...: {e}")
            self.cache.stats.errors += 1
            return None

    def exists(self, sha256_hash: str) -> bool:
        """
        Check if image is available (in cache or source).

        Args:
            sha256_hash: SHA256 hash of image

        Returns:
            True if image is available
        """
        # Check cache first
        if self.cache.get(sha256_hash):
            return True

        # Check source
        return self.source.exists(sha256_hash)

    def warmup(self, sha256_hashes: list, max_workers: int = 4):
        """
        Pre-download and cache a list of images.

        Args:
            sha256_hashes: List of SHA256 hashes to download
            max_workers: Number of parallel downloads
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        logger.info(f"Warming up cache with {len(sha256_hashes)} images...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.get_image_path, sha_hash): sha_hash
                for sha_hash in sha256_hashes
            }

            completed = 0
            for future in as_completed(futures):
                sha_hash = futures[future]
                try:
                    result = future.result()
                    if result:
                        completed += 1
                except Exception as e:
                    logger.error(f"Warmup error for {sha_hash[:16]}...: {e}")

        logger.info(f"Cache warmup complete: {completed}/{len(sha256_hashes)} successful")

    def get_stats(self) -> dict:
        """Get combined statistics for cache and source."""
        stats = self.cache.get_stats()

        if self.registry:
            registry_stats = self.registry.get_stats()
            stats["registry"] = registry_stats

        return stats


def create_cached_source(
    source: ImageSource,
    cache_dir: Optional[Path] = None,
    registry_path: Optional[Path] = None,
    cache_ttl: int = 14400,  # 4 hours
    source_name: str = "default",
) -> CachedImageSource:
    """
    Factory function to create a cached image source.

    Args:
        source: Underlying ImageSource
        cache_dir: Cache directory (default: /tmp/imgcache)
        registry_path: Path registry file (default: .image_path_registry.json)
        cache_ttl: Cache TTL in seconds
        source_name: Name for source identification

    Returns:
        Configured CachedImageSource
    """
    from .jit_cache import DEFAULT_CACHE_DIR
    from .path_registry import DEFAULT_REGISTRY_PATH

    cache = JITImageCache(
        cache_dir=cache_dir or DEFAULT_CACHE_DIR,
        default_ttl_seconds=cache_ttl,
    )

    registry = None
    if registry_path or registry_path is not False:
        registry = ImagePathRegistry(registry_path or DEFAULT_REGISTRY_PATH)

    return CachedImageSource(
        source=source,
        cache=cache,
        registry=registry,
        source_name=source_name,
    )
