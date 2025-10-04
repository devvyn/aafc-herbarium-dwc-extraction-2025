"""AWS S3 storage backend."""

import boto3
from botocore.exceptions import ClientError
from pathlib import Path
from typing import Iterator, Optional

from ..locator import ImageLocator, ImageMetadata


class S3ImageLocator:
    """ImageLocator implementation for AWS S3 storage.

    Fetches images from S3 buckets. For local caching, wrap with
    CachingImageLocator decorator.

    Args:
        bucket: S3 bucket name
        prefix: Optional S3 key prefix (e.g., "images/herbarium/")
        region: AWS region (default: us-east-1)

    Example:
        # Direct S3 access (no caching)
        locator = S3ImageLocator(bucket="my-bucket", prefix="images/")
        image_data = locator.get_image("specimen_001.jpg")
        # Fetches s3://my-bucket/images/specimen_001.jpg

        # With transparent caching
        locator = CachingImageLocator(
            S3ImageLocator(bucket="my-bucket"),
            cache_dir=Path("/tmp/image-cache")
        )
        image_data = locator.get_image("specimen_001.jpg")  # Cached locally
    """

    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        region: str = "us-east-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ):
        """Initialize S3 image locator.

        Args:
            bucket: S3 bucket name
            prefix: Optional S3 key prefix (e.g., "images/herbarium/")
            region: AWS region (default: us-east-1)
            aws_access_key_id: Optional AWS access key (uses default credentials if None)
            aws_secret_access_key: Optional AWS secret key (uses default credentials if None)
        """
        self.bucket = bucket
        self.prefix = prefix.rstrip("/") + "/" if prefix else ""
        self.region = region

        # Initialize S3 client
        session_kwargs = {"region_name": region}
        if aws_access_key_id and aws_secret_access_key:
            session_kwargs["aws_access_key_id"] = aws_access_key_id
            session_kwargs["aws_secret_access_key"] = aws_secret_access_key

        self.s3_client = boto3.client("s3", **session_kwargs)

    def _get_s3_key(self, identifier: str) -> str:
        """Convert identifier to full S3 key.

        Args:
            identifier: Relative identifier (e.g., "specimen_001.jpg")

        Returns:
            Full S3 key (e.g., "images/herbarium/specimen_001.jpg")
        """
        return f"{self.prefix}{identifier}"

    def exists(self, identifier: str) -> bool:
        """Check if an image exists in S3.

        Args:
            identifier: Relative identifier (e.g., "specimen_001.jpg")

        Returns:
            True if object exists in S3 bucket
        """
        key = self._get_s3_key(identifier)
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    def get_image(self, identifier: str) -> bytes:
        """Retrieve image data from S3.

        Args:
            identifier: Relative identifier (e.g., "specimen_001.jpg")

        Returns:
            Raw image bytes

        Raises:
            FileNotFoundError: S3 object does not exist
            PermissionError: Access denied to S3 object
            IOError: Network error or other S3 error
        """
        key = self._get_s3_key(identifier)
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "NoSuchKey":
                raise FileNotFoundError(f"Image not found in S3: {identifier}")
            elif error_code == "403":
                raise PermissionError(f"Access denied to S3 object: {identifier}")
            else:
                raise IOError(f"S3 error: {e}")

    def get_metadata(self, identifier: str) -> ImageMetadata:
        """Get metadata about an S3 object.

        Args:
            identifier: Relative identifier (e.g., "specimen_001.jpg")

        Returns:
            ImageMetadata with S3 object information

        Raises:
            FileNotFoundError: S3 object does not exist
        """
        key = self._get_s3_key(identifier)
        try:
            response = self.s3_client.head_object(Bucket=self.bucket, Key=key)
            return ImageMetadata(
                identifier=identifier,
                size_bytes=response.get("ContentLength"),
                last_modified=response.get("LastModified").timestamp() if response.get("LastModified") else None,
                content_type=response.get("ContentType"),
                source_uri=f"s3://{self.bucket}/{key}",
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise FileNotFoundError(f"Image not found in S3: {identifier}")
            raise

    def list_images(self, prefix: Optional[str] = None) -> Iterator[str]:
        """List available images in S3 bucket.

        Args:
            prefix: Optional additional prefix filter (appended to self.prefix)

        Yields:
            Relative identifiers for objects in S3 bucket

        Note:
            Only yields objects with common image extensions:
            .jpg, .jpeg, .png, .tif, .tiff, .bmp, .gif
        """
        image_extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif"}

        # Combine prefixes
        search_prefix = self.prefix
        if prefix:
            search_prefix = f"{self.prefix}{prefix.rstrip('/')}/"

        # Use paginator for large buckets
        paginator = self.s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.bucket, Prefix=search_prefix)

        for page in pages:
            if "Contents" not in page:
                continue

            for obj in page["Contents"]:
                key = obj["Key"]
                # Check if object has image extension
                if any(key.lower().endswith(ext) for ext in image_extensions):
                    # Return identifier relative to self.prefix
                    if key.startswith(self.prefix):
                        identifier = key[len(self.prefix):]
                        yield identifier

    def get_local_path(self, identifier: str) -> Optional[Path]:
        """Get local filesystem path for an S3 image.

        For S3ImageLocator, this always returns None since images are remote.
        Use CachingImageLocator wrapper for automatic local caching.

        Args:
            identifier: Relative identifier

        Returns:
            None (images are in S3, not local filesystem)
        """
        return None
