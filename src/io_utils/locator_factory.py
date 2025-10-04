"""Factory for creating ImageLocator instances from configuration.

This module provides the bridge between the configuration file and the
storage abstraction layer. It instantiates the appropriate ImageLocator
backend (local filesystem, S3, MinIO, HTTP) based on configuration.

Example:
    # In cli.py or other entry points
    locator = create_image_locator(config, input_path)
    for identifier in locator.list_images():
        image_data = locator.get_image(identifier)
        # Process image...
"""

from pathlib import Path
from typing import Dict, Any, Optional

from .locator import ImageLocator
from .locators.local import LocalFilesystemLocator
from .caching import CachingImageLocator


def create_image_locator(
    config: Dict[str, Any],
    input_path: Optional[Path] = None,
) -> ImageLocator:
    """Create an ImageLocator instance from configuration.

    This factory function examines the config to determine which storage
    backend to use, then instantiates and configures it appropriately.

    Configuration format (TOML):
    ```toml
    [storage]
    # Backend type: "local", "s3", "minio", "http"
    backend = "local"

    # Optional: Enable caching for remote backends
    cache_enabled = true
    cache_dir = "/tmp/image-cache"
    cache_max_size_mb = 1000

    # Backend-specific settings
    [storage.s3]
    bucket = "my-bucket"
    prefix = "images/herbarium/"
    region = "us-east-1"

    [storage.minio]
    endpoint = "http://localhost:9000"
    bucket = "my-bucket"
    access_key = "minioadmin"
    secret_key = "minioadmin"
    ```

    Args:
        config: Configuration dictionary (from TOML)
        input_path: Optional path for local filesystem backend (legacy support)

    Returns:
        ImageLocator instance configured according to config

    Raises:
        ValueError: Invalid or missing configuration
        ImportError: Required backend dependencies not installed

    Examples:
        # Local filesystem (legacy mode - no [storage] section)
        locator = create_image_locator(config, Path("/data/images"))

        # Local filesystem (explicit config)
        config = {"storage": {"backend": "local", "base_path": "/data/images"}}
        locator = create_image_locator(config)

        # S3 with caching
        config = {
            "storage": {
                "backend": "s3",
                "cache_enabled": True,
                "cache_dir": "/tmp/cache",
                "s3": {"bucket": "my-bucket", "prefix": "images/"}
            }
        }
        locator = create_image_locator(config)
    """
    storage_cfg = config.get("storage", {})
    backend_type = storage_cfg.get("backend", "local")

    # Create base locator
    if backend_type == "local":
        base_path = storage_cfg.get("base_path")
        if base_path is None:
            if input_path is None:
                raise ValueError("Local backend requires 'base_path' in config or input_path argument")
            base_path = input_path
        else:
            base_path = Path(base_path)

        locator: ImageLocator = LocalFilesystemLocator(base_path)

    elif backend_type == "s3":
        # Import S3 backend (lazy import to avoid boto3 dependency if not needed)
        try:
            from .locators.s3 import S3ImageLocator
        except ImportError as e:
            raise ImportError(
                "S3 backend requires boto3: pip install boto3"
            ) from e

        s3_cfg = storage_cfg.get("s3", {})
        if "bucket" not in s3_cfg:
            raise ValueError("S3 backend requires 'storage.s3.bucket' in config")

        locator = S3ImageLocator(
            bucket=s3_cfg["bucket"],
            prefix=s3_cfg.get("prefix", ""),
            region=s3_cfg.get("region", "us-east-1"),
            aws_access_key_id=s3_cfg.get("access_key_id"),
            aws_secret_access_key=s3_cfg.get("secret_access_key"),
        )

    elif backend_type == "minio":
        # MinIO is S3-compatible, use S3ImageLocator with custom endpoint
        try:
            from .locators.s3 import S3ImageLocator
            import boto3
        except ImportError as e:
            raise ImportError(
                "MinIO backend requires boto3: pip install boto3"
            ) from e

        minio_cfg = storage_cfg.get("minio", {})
        if "endpoint" not in minio_cfg or "bucket" not in minio_cfg:
            raise ValueError("MinIO backend requires 'endpoint' and 'bucket' in storage.minio config")

        # Create boto3 client with MinIO endpoint
        s3_client = boto3.client(
            "s3",
            endpoint_url=minio_cfg["endpoint"],
            aws_access_key_id=minio_cfg.get("access_key", "minioadmin"),
            aws_secret_access_key=minio_cfg.get("secret_key", "minioadmin"),
            region_name=minio_cfg.get("region", "us-east-1"),
        )

        # Create S3ImageLocator but inject custom client
        locator = S3ImageLocator(
            bucket=minio_cfg["bucket"],
            prefix=minio_cfg.get("prefix", ""),
            region=minio_cfg.get("region", "us-east-1"),
            aws_access_key_id=minio_cfg.get("access_key"),
            aws_secret_access_key=minio_cfg.get("secret_key"),
        )
        # Override with custom client
        locator.s3_client = s3_client

    elif backend_type == "http":
        raise NotImplementedError("HTTP backend not yet implemented")

    else:
        raise ValueError(f"Unknown storage backend: {backend_type}")

    # Wrap with caching if enabled
    if storage_cfg.get("cache_enabled", False):
        cache_dir = storage_cfg.get("cache_dir")
        if cache_dir is None:
            raise ValueError("Caching enabled but 'cache_dir' not specified in storage config")

        cache_dir = Path(cache_dir)
        max_size_mb = storage_cfg.get("cache_max_size_mb")

        locator = CachingImageLocator(
            locator,
            cache_dir=cache_dir,
            max_cache_size_mb=max_size_mb,
        )

    return locator
