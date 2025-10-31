"""
Manifest-Based Image Path Registry

Tracks known locations for specimen images across multiple sources
with priority ordering and manifest versioning for reproducibility.

Features:
- SHA256-based image identification
- Multiple location tracking per image
- Priority-ordered lookups (cache → local → S3)
- Manifest versioning for reproducibility
- Integration with ImageSource abstraction
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ImageLocation:
    """Represents a known location for an image."""

    sha256_hash: str
    location_type: str  # "cache", "local", "s3", "http"
    path: str  # Local path, S3 URI, or HTTP URL
    verified_at: Optional[float] = None  # Unix timestamp of last verification
    size_bytes: Optional[int] = None
    source_manifest: Optional[str] = None  # Which manifest registered this location

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "sha256_hash": self.sha256_hash,
            "location_type": self.location_type,
            "path": self.path,
            "verified_at": self.verified_at,
            "size_bytes": self.size_bytes,
            "source_manifest": self.source_manifest,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ImageLocation":
        """Create from dictionary."""
        return cls(
            sha256_hash=data["sha256_hash"],
            location_type=data["location_type"],
            path=data["path"],
            verified_at=data.get("verified_at"),
            size_bytes=data.get("size_bytes"),
            source_manifest=data.get("source_manifest"),
        )


class ImagePathRegistry:
    """
    Registry tracking known locations for specimen images.

    Maintains a centralized index of where each image can be found,
    supporting priority-ordered lookups and manifest versioning.
    """

    # Priority order for location types (higher = preferred)
    LOCATION_PRIORITY = {
        "cache": 100,  # Fastest: in-memory or local cache
        "local": 80,  # Fast: local filesystem
        "persistent": 60,  # Medium: persistent local storage
        "s3": 40,  # Slower: S3 with network latency
        "http": 20,  # Slowest: HTTP download
    }

    def __init__(self, registry_path: Path):
        """
        Initialize image path registry.

        Args:
            registry_path: Path to registry JSON file
        """
        self.registry_path = Path(registry_path)
        self._locations: Dict[str, List[ImageLocation]] = {}
        self._manifests: Dict[str, dict] = {}

        # Ensure parent directory exists
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing registry
        self._load()

        logger.info(f"Path registry initialized: {len(self._locations)} images tracked")

    def _load(self):
        """Load registry from disk."""
        if not self.registry_path.exists():
            logger.info(f"No existing registry at {self.registry_path}")
            return

        try:
            with open(self.registry_path) as f:
                data = json.load(f)

            # Load locations
            for sha_hash, locations_data in data.get("locations", {}).items():
                self._locations[sha_hash] = [
                    ImageLocation.from_dict(loc_data) for loc_data in locations_data
                ]

            # Load manifests
            self._manifests = data.get("manifests", {})

            logger.info(
                f"Loaded registry: {len(self._locations)} images, {len(self._manifests)} manifests"
            )

        except Exception as e:
            logger.error(f"Failed to load registry: {e}")
            # Start fresh
            self._locations = {}
            self._manifests = {}

    def _save(self):
        """Save registry to disk."""
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "locations": {
                    sha_hash: [loc.to_dict() for loc in locations]
                    for sha_hash, locations in self._locations.items()
                },
                "manifests": self._manifests,
            }

            # Atomic write (write to temp, then rename)
            temp_path = self.registry_path.with_suffix(".tmp")
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2)

            temp_path.replace(self.registry_path)

            logger.debug(f"Saved registry: {len(self._locations)} images")

        except Exception as e:
            logger.error(f"Failed to save registry: {e}")

    def register_location(
        self,
        sha256_hash: str,
        location_type: str,
        path: str,
        size_bytes: Optional[int] = None,
        source_manifest: Optional[str] = None,
        verified: bool = True,
    ):
        """
        Register a known location for an image.

        Args:
            sha256_hash: SHA256 hash of image
            location_type: Type of location ("cache", "local", "s3", "http")
            path: Path/URI/URL to image
            size_bytes: File size if known
            source_manifest: Manifest ID that registered this location
            verified: Whether location has been verified to exist
        """
        # Create location object
        location = ImageLocation(
            sha256_hash=sha256_hash,
            location_type=location_type,
            path=path,
            verified_at=datetime.now().timestamp() if verified else None,
            size_bytes=size_bytes,
            source_manifest=source_manifest,
        )

        # Get or create locations list for this hash
        if sha256_hash not in self._locations:
            self._locations[sha256_hash] = []

        # Check if this location already exists
        existing = [
            loc
            for loc in self._locations[sha256_hash]
            if loc.location_type == location_type and loc.path == path
        ]

        if existing:
            # Update existing location
            existing[0].verified_at = location.verified_at
            existing[0].size_bytes = size_bytes or existing[0].size_bytes
        else:
            # Add new location
            self._locations[sha256_hash].append(location)

        logger.debug(f"Registered location: {sha256_hash[:16]}... @ {location_type}:{path[:50]}")

        # Auto-save after modifications
        self._save()

    def get_locations(self, sha256_hash: str, verified_only: bool = False) -> List[ImageLocation]:
        """
        Get all known locations for an image, sorted by priority.

        Args:
            sha256_hash: SHA256 hash of image
            verified_only: Only return verified locations

        Returns:
            List of locations, sorted by priority (highest first)
        """
        locations = self._locations.get(sha256_hash, [])

        if verified_only:
            locations = [loc for loc in locations if loc.verified_at is not None]

        # Sort by priority (highest first)
        return sorted(
            locations,
            key=lambda loc: self.LOCATION_PRIORITY.get(loc.location_type, 0),
            reverse=True,
        )

    def get_best_location(self, sha256_hash: str) -> Optional[ImageLocation]:
        """
        Get highest-priority location for an image.

        Args:
            sha256_hash: SHA256 hash of image

        Returns:
            Highest-priority location, or None if not found
        """
        locations = self.get_locations(sha256_hash, verified_only=False)
        return locations[0] if locations else None

    def has_image(self, sha256_hash: str) -> bool:
        """Check if image has any registered locations."""
        return sha256_hash in self._locations and len(self._locations[sha256_hash]) > 0

    def register_manifest(
        self,
        manifest_id: str,
        manifest_path: Optional[Path] = None,
        metadata: Optional[dict] = None,
    ):
        """
        Register a manifest file.

        Args:
            manifest_id: Unique manifest identifier
            manifest_path: Path to manifest file
            metadata: Additional manifest metadata
        """
        self._manifests[manifest_id] = {
            "id": manifest_id,
            "path": str(manifest_path) if manifest_path else None,
            "registered_at": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        logger.info(f"Registered manifest: {manifest_id}")
        self._save()

    def load_manifest(self, manifest_path: Path) -> dict:
        """
        Load and register locations from a manifest file.

        Expected manifest format:
        {
            "manifest_id": "extraction_run_20251010",
            "images": [
                {
                    "sha256_hash": "abc123...",
                    "locations": [
                        {"type": "s3", "path": "s3://bucket/images/..."},
                        {"type": "local", "path": "/tmp/imgcache/..."}
                    ],
                    "size_bytes": 12345
                }
            ]
        }

        Args:
            manifest_path: Path to manifest JSON file

        Returns:
            Loaded manifest data
        """
        with open(manifest_path) as f:
            manifest = json.load(f)

        manifest_id = manifest.get("manifest_id", manifest_path.stem)

        # Register manifest
        self.register_manifest(
            manifest_id,
            manifest_path=manifest_path,
            metadata=manifest.get("metadata", {}),
        )

        # Register all image locations
        images = manifest.get("images", [])
        registered_count = 0

        for image_data in images:
            sha_hash = image_data.get("sha256_hash")
            if not sha_hash:
                continue

            size_bytes = image_data.get("size_bytes")

            for location_data in image_data.get("locations", []):
                self.register_location(
                    sha256_hash=sha_hash,
                    location_type=location_data.get("type", "unknown"),
                    path=location_data.get("path", ""),
                    size_bytes=size_bytes,
                    source_manifest=manifest_id,
                    verified=location_data.get("verified", False),
                )
                registered_count += 1

        logger.info(
            f"Loaded manifest {manifest_id}: {len(images)} images, {registered_count} locations"
        )

        return manifest

    def export_manifest(self, output_path: Path, sha256_hashes: Optional[List[str]] = None):
        """
        Export current registry as a manifest file.

        Args:
            output_path: Path to save manifest
            sha256_hashes: List of hashes to export (None = all)
        """
        hashes = sha256_hashes or list(self._locations.keys())

        images = []
        for sha_hash in hashes:
            locations = self._locations.get(sha_hash, [])
            if not locations:
                continue

            images.append(
                {
                    "sha256_hash": sha_hash,
                    "locations": [
                        {
                            "type": loc.location_type,
                            "path": loc.path,
                            "verified": loc.verified_at is not None,
                        }
                        for loc in locations
                    ],
                    "size_bytes": next(
                        (loc.size_bytes for loc in locations if loc.size_bytes), None
                    ),
                }
            )

        manifest = {
            "manifest_id": output_path.stem,
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "image_count": len(images),
            "images": images,
        }

        with open(output_path, "w") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Exported manifest: {output_path} ({len(images)} images)")

    def get_stats(self) -> dict:
        """Get registry statistics."""
        location_type_counts = {}
        for locations in self._locations.values():
            for loc in locations:
                location_type_counts[loc.location_type] = (
                    location_type_counts.get(loc.location_type, 0) + 1
                )

        return {
            "total_images": len(self._locations),
            "total_locations": sum(len(locs) for locs in self._locations.values()),
            "manifests": len(self._manifests),
            "location_types": location_type_counts,
        }


# Default registry location
DEFAULT_REGISTRY_PATH = Path(".image_path_registry.json")
