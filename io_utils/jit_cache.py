"""
JIT (Just-In-Time) Image Cache with TTL and Graceful Error Handling

Provides temporary caching of specimen images with automatic cleanup
and graceful degradation when cache files are missing (e.g., /tmp cleanup).

Features:
- TTL-based cache expiration
- Automatic cleanup of expired entries
- Graceful fallback to re-download on missing files
- Integration with ImageSource abstraction
- Event emission for monitoring
"""

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached image with metadata."""

    sha256_hash: str
    local_path: Path
    cached_at: float  # Unix timestamp
    ttl_seconds: int
    source: str  # e.g., "s3", "local"
    size_bytes: int = 0

    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        age = time.time() - self.cached_at
        return age > self.ttl_seconds

    def exists(self) -> bool:
        """Check if the cached file still exists on disk."""
        return self.local_path.exists()

    def age_seconds(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.cached_at


@dataclass
class CacheStats:
    """Statistics for cache performance."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    downloads: int = 0
    errors: int = 0
    total_size_bytes: int = 0

    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0


class JITImageCache:
    """
    Just-In-Time image cache with TTL and graceful error handling.

    Caches images temporarily with configurable TTL. Automatically handles
    missing files (e.g., /tmp cleanup) by re-downloading from source.
    """

    def __init__(
        self,
        cache_dir: Path,
        default_ttl_seconds: int = 14400,  # 4 hours default
        max_cache_size_gb: float = 10.0,
        auto_cleanup: bool = True,
    ):
        """
        Initialize JIT cache.

        Args:
            cache_dir: Directory for cached files
            default_ttl_seconds: Default TTL for cache entries (default: 4 hours)
            max_cache_size_gb: Maximum cache size in GB
            auto_cleanup: Automatically cleanup expired entries
        """
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl_seconds
        self.max_cache_size = max_cache_size_gb * 1024 * 1024 * 1024  # Convert to bytes
        self.auto_cleanup = auto_cleanup

        # In-memory cache registry
        self._entries: Dict[str, CacheEntry] = {}

        # Statistics
        self.stats = CacheStats()

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load existing cache metadata if available
        self._load_metadata()

        logger.info(
            f"JIT cache initialized: {self.cache_dir} (TTL: {self.default_ttl}s, "
            f"max size: {max_cache_size_gb}GB)"
        )

    def _metadata_path(self) -> Path:
        """Get path to cache metadata file."""
        return self.cache_dir / "cache_metadata.json"

    def _load_metadata(self):
        """Load cache metadata from disk."""
        metadata_file = self._metadata_path()
        if not metadata_file.exists():
            return

        try:
            with open(metadata_file) as f:
                data = json.load(f)

            # Reconstruct cache entries
            for sha_hash, entry_data in data.get("entries", {}).items():
                entry = CacheEntry(
                    sha256_hash=sha_hash,
                    local_path=Path(entry_data["local_path"]),
                    cached_at=entry_data["cached_at"],
                    ttl_seconds=entry_data["ttl_seconds"],
                    source=entry_data["source"],
                    size_bytes=entry_data.get("size_bytes", 0),
                )

                # Only keep if file still exists and not expired
                if entry.exists() and not entry.is_expired():
                    self._entries[sha_hash] = entry

            # Load statistics
            if "stats" in data:
                stats_data = data["stats"]
                self.stats = CacheStats(**stats_data)

            logger.info(f"Loaded {len(self._entries)} cache entries from metadata")

        except Exception as e:
            logger.warning(f"Failed to load cache metadata: {e}")

    def _save_metadata(self):
        """Save cache metadata to disk."""
        try:
            # Clean up expired/missing entries before saving
            if self.auto_cleanup:
                self._cleanup_expired()

            data = {
                "entries": {
                    sha_hash: {
                        "local_path": str(entry.local_path),
                        "cached_at": entry.cached_at,
                        "ttl_seconds": entry.ttl_seconds,
                        "source": entry.source,
                        "size_bytes": entry.size_bytes,
                    }
                    for sha_hash, entry in self._entries.items()
                },
                "stats": {
                    "hits": self.stats.hits,
                    "misses": self.stats.misses,
                    "evictions": self.stats.evictions,
                    "downloads": self.stats.downloads,
                    "errors": self.stats.errors,
                    "total_size_bytes": self.stats.total_size_bytes,
                },
                "saved_at": datetime.now().isoformat(),
            }

            with open(self._metadata_path(), "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.warning(f"Failed to save cache metadata: {e}")

    def _cleanup_expired(self):
        """Remove expired cache entries."""
        expired = [sha_hash for sha_hash, entry in self._entries.items() if entry.is_expired()]

        for sha_hash in expired:
            entry = self._entries[sha_hash]
            # Try to delete file
            if entry.local_path.exists():
                try:
                    entry.local_path.unlink()
                    self.stats.evictions += 1
                    logger.debug(f"Evicted expired cache entry: {sha_hash[:16]}...")
                except Exception as e:
                    logger.warning(f"Failed to delete expired cache file: {e}")

            # Remove from registry
            del self._entries[sha_hash]

    def _check_size_limit(self):
        """Evict oldest entries if cache exceeds size limit."""
        current_size = sum(entry.size_bytes for entry in self._entries.values())

        if current_size > self.max_cache_size:
            # Sort entries by age (oldest first)
            sorted_entries = sorted(self._entries.items(), key=lambda x: x[1].cached_at)

            # Evict until under limit
            for sha_hash, entry in sorted_entries:
                if current_size <= self.max_cache_size * 0.9:  # 90% threshold
                    break

                # Delete file
                if entry.local_path.exists():
                    try:
                        current_size -= entry.size_bytes
                        entry.local_path.unlink()
                        self.stats.evictions += 1
                        logger.debug(f"Evicted for size limit: {sha_hash[:16]}...")
                    except Exception as e:
                        logger.warning(f"Failed to delete cache file: {e}")

                # Remove from registry
                del self._entries[sha_hash]

    def get(self, sha256_hash: str) -> Optional[Path]:
        """
        Get cached image path if available and valid.

        Args:
            sha256_hash: SHA256 hash of image

        Returns:
            Path to cached file if valid, None otherwise
        """
        # Check if in cache registry
        if sha256_hash not in self._entries:
            self.stats.misses += 1
            return None

        entry = self._entries[sha256_hash]

        # Check if expired
        if entry.is_expired():
            logger.debug(
                f"Cache entry expired: {sha256_hash[:16]}... (age: {entry.age_seconds():.0f}s)"
            )
            del self._entries[sha256_hash]
            self.stats.misses += 1
            return None

        # Check if file still exists (graceful handling of /tmp cleanup)
        if not entry.exists():
            logger.warning(f"Cache file missing (possibly /tmp cleanup): {entry.local_path}")
            del self._entries[sha256_hash]
            self.stats.misses += 1
            return None

        # Valid cache hit
        self.stats.hits += 1
        logger.debug(f"Cache hit: {sha256_hash[:16]}... (age: {entry.age_seconds():.0f}s)")
        return entry.local_path

    def put(
        self,
        sha256_hash: str,
        local_path: Path,
        source: str = "unknown",
        ttl_seconds: Optional[int] = None,
    ):
        """
        Add image to cache.

        Args:
            sha256_hash: SHA256 hash of image
            local_path: Path to cached file
            source: Source of image (e.g., "s3", "local")
            ttl_seconds: TTL override (uses default if None)
        """
        if not local_path.exists():
            logger.warning(f"Cannot cache non-existent file: {local_path}")
            return

        # Get file size
        size_bytes = local_path.stat().st_size

        # Create cache entry
        entry = CacheEntry(
            sha256_hash=sha256_hash,
            local_path=local_path,
            cached_at=time.time(),
            ttl_seconds=ttl_seconds or self.default_ttl,
            source=source,
            size_bytes=size_bytes,
        )

        # Add to registry
        self._entries[sha256_hash] = entry
        self.stats.total_size_bytes += size_bytes

        # Check size limits
        if self.auto_cleanup:
            self._check_size_limit()

        logger.debug(
            f"Cached image: {sha256_hash[:16]}... "
            f"({size_bytes / 1024:.1f} KB, TTL: {entry.ttl_seconds}s)"
        )

    def remove(self, sha256_hash: str):
        """Remove image from cache."""
        if sha256_hash in self._entries:
            entry = self._entries[sha256_hash]

            # Delete file
            if entry.local_path.exists():
                try:
                    entry.local_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete cache file: {e}")

            # Remove from registry
            del self._entries[sha256_hash]

    def clear(self):
        """Clear entire cache."""
        for sha_hash in list(self._entries.keys()):
            self.remove(sha_hash)

        self.stats = CacheStats()
        logger.info("Cache cleared")

    def get_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "hit_rate": self.stats.hit_rate(),
            "evictions": self.stats.evictions,
            "downloads": self.stats.downloads,
            "errors": self.stats.errors,
            "entries": len(self._entries),
            "total_size_mb": self.stats.total_size_bytes / (1024 * 1024),
        }

    def __del__(self):
        """Save metadata on object destruction."""
        try:
            self._save_metadata()
        except Exception:
            pass  # Best effort


# Default cache configuration
DEFAULT_CACHE_DIR = Path("/tmp/imgcache")
DEFAULT_TTL_SECONDS = 14400  # 4 hours
