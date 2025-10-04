"""Storage backend implementations for ImageLocator protocol.

Available backends:
- LocalFilesystemLocator: Local filesystem storage
- S3ImageLocator: AWS S3 storage
- MinIOImageLocator: MinIO object storage (S3-compatible)
- HTTPImageLocator: Fetch images via HTTP/HTTPS (read-only)
"""

from .local import LocalFilesystemLocator
from .s3 import S3ImageLocator

__all__ = ["LocalFilesystemLocator", "S3ImageLocator"]
