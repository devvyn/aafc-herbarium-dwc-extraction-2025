"""Image source abstraction for S3 and local filesystem interchangeability.

Provides a unified interface for accessing herbarium images whether stored
in S3 buckets or local filesystem, using SHA256 hashes as the key.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union, List
import subprocess
import hashlib
import requests
from urllib.parse import urlparse
import tempfile
import os


class ImageSource(ABC):
    """Abstract base class for image sources."""

    @abstractmethod
    def get_image_path(self, sha256_hash: str) -> Optional[str]:
        """Get the path/URL to an image given its SHA256 hash.

        Args:
            sha256_hash: SHA256 hash of the image (64 hex characters)

        Returns:
            Path/URL to the image, or None if not found
        """
        pass

    @abstractmethod
    def download_image(self, sha256_hash: str, local_path: Path) -> bool:
        """Download an image to a local path.

        Args:
            sha256_hash: SHA256 hash of the image
            local_path: Where to save the image locally

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def exists(self, sha256_hash: str) -> bool:
        """Check if an image exists in this source.

        Args:
            sha256_hash: SHA256 hash of the image

        Returns:
            True if the image exists, False otherwise
        """
        pass


class S3ImageSource(ImageSource):
    """Image source backed by S3 bucket with SHA256-based organization."""

    def __init__(self, bucket: str, region: str = "ca-central-1", prefix: str = "images"):
        """Initialize S3 image source.

        Args:
            bucket: S3 bucket name
            region: AWS region
            prefix: Path prefix in bucket (default: "images")
        """
        self.bucket = bucket
        self.region = region
        self.prefix = prefix
        self.base_url = f"https://s3.{region}.amazonaws.com/{bucket}"

    def _hash_to_path(self, sha256_hash: str) -> str:
        """Convert SHA256 hash to S3 path structure.

        Args:
            sha256_hash: 64-character SHA256 hex string

        Returns:
            S3 key path like "images/00/0e/000e426d...c84.jpg"
        """
        if len(sha256_hash) != 64:
            raise ValueError(f"Invalid SHA256 hash length: {len(sha256_hash)}")

        return f"{self.prefix}/{sha256_hash[:2]}/{sha256_hash[2:4]}/{sha256_hash}.jpg"

    def get_image_path(self, sha256_hash: str) -> Optional[str]:
        """Get S3 URL for an image."""
        try:
            s3_key = self._hash_to_path(sha256_hash)
            return f"{self.base_url}/{s3_key}"
        except ValueError:
            return None

    def get_s3_uri(self, sha256_hash: str) -> Optional[str]:
        """Get S3 URI (s3://) for an image."""
        try:
            s3_key = self._hash_to_path(sha256_hash)
            return f"s3://{self.bucket}/{s3_key}"
        except ValueError:
            return None

    def download_image(self, sha256_hash: str, local_path: Path) -> bool:
        """Download image from S3 using AWS CLI."""
        s3_uri = self.get_s3_uri(sha256_hash)
        if not s3_uri:
            return False

        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            result = subprocess.run([
                'aws', 's3', 'cp', s3_uri, str(local_path)
            ], capture_output=True, text=True, check=True)
            return local_path.exists()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def exists(self, sha256_hash: str) -> bool:
        """Check if image exists in S3."""
        s3_uri = self.get_s3_uri(sha256_hash)
        if not s3_uri:
            return False

        try:
            result = subprocess.run([
                'aws', 's3', 'ls', s3_uri
            ], capture_output=True, text=True, check=True)
            return len(result.stdout.strip()) > 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


class LocalImageSource(ImageSource):
    """Image source backed by local filesystem with SHA256-based organization."""

    def __init__(self, base_path: Union[str, Path]):
        """Initialize local image source.

        Args:
            base_path: Base directory containing images
        """
        self.base_path = Path(base_path)

    def _hash_to_path(self, sha256_hash: str) -> Path:
        """Convert SHA256 hash to local path structure.

        Args:
            sha256_hash: 64-character SHA256 hex string

        Returns:
            Local path like "base/00/0e/000e426d...c84.jpg"
        """
        if len(sha256_hash) != 64:
            raise ValueError(f"Invalid SHA256 hash length: {len(sha256_hash)}")

        return (self.base_path /
                sha256_hash[:2] /
                sha256_hash[2:4] /
                f"{sha256_hash}.jpg")

    def get_image_path(self, sha256_hash: str) -> Optional[str]:
        """Get local filesystem path for an image."""
        try:
            path = self._hash_to_path(sha256_hash)
            return str(path) if path.exists() else None
        except ValueError:
            return None

    def download_image(self, sha256_hash: str, local_path: Path) -> bool:
        """Copy image from one local path to another."""
        source_path = self.get_image_path(sha256_hash)
        if not source_path:
            return False

        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(['cp', source_path, str(local_path)], check=True)
            return local_path.exists()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def exists(self, sha256_hash: str) -> bool:
        """Check if image exists locally."""
        try:
            path = self._hash_to_path(sha256_hash)
            return path.exists()
        except ValueError:
            return False


class MultiImageSource(ImageSource):
    """Image source that tries multiple sources in priority order."""

    def __init__(self, sources: List[ImageSource]):
        """Initialize multi-source with priority order.

        Args:
            sources: List of image sources in priority order
        """
        self.sources = sources

    def get_image_path(self, sha256_hash: str) -> Optional[str]:
        """Get path from first available source."""
        for source in self.sources:
            path = source.get_image_path(sha256_hash)
            if path:
                return path
        return None

    def download_image(self, sha256_hash: str, local_path: Path) -> bool:
        """Download from first available source."""
        for source in self.sources:
            if source.exists(sha256_hash):
                return source.download_image(sha256_hash, local_path)
        return False

    def exists(self, sha256_hash: str) -> bool:
        """Check if image exists in any source."""
        return any(source.exists(sha256_hash) for source in self.sources)


class ImageSourceConfig:
    """Configuration-based image source factory."""

    @staticmethod
    def from_config(config_dict: dict) -> ImageSource:
        """Create image source from configuration dictionary.

        Args:
            config_dict: Configuration with source type and parameters

        Returns:
            Configured ImageSource instance
        """
        source_type = config_dict.get('type', 's3')

        if source_type == 's3':
            return S3ImageSource(
                bucket=config_dict['bucket'],
                region=config_dict.get('region', 'ca-central-1'),
                prefix=config_dict.get('prefix', 'images')
            )
        elif source_type == 'local':
            return LocalImageSource(config_dict['base_path'])
        elif source_type == 'multi':
            sources = [
                ImageSourceConfig.from_config(src_config)
                for src_config in config_dict['sources']
            ]
            return MultiImageSource(sources)
        else:
            raise ValueError(f"Unknown source type: {source_type}")


def calculate_sha256(file_path: Union[str, Path]) -> str:
    """Calculate SHA256 hash of a file.

    Args:
        file_path: Path to file

    Returns:
        SHA256 hash as hex string
    """
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


# Default configurations
DEFAULT_S3_CONFIG = {
    'type': 's3',
    'bucket': 'devvyn.aafc-srdc.herbarium',
    'region': 'ca-central-1',
    'prefix': 'images'
}

DEFAULT_MULTI_CONFIG = {
    'type': 'multi',
    'sources': [
        {
            'type': 'local',
            'base_path': './images'
        },
        DEFAULT_S3_CONFIG
    ]
}
