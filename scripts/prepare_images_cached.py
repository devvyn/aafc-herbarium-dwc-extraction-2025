#!/usr/bin/env python3
"""
Prepare Images for Extraction with Robust Caching

Downloads specimen images from S3 with JIT caching and path registry.
Handles /tmp cleanup gracefully by tracking all image locations.

Usage:
    python scripts/prepare_images_cached.py \\
        --bucket devvyn.aafc-srdc.herbarium \\
        --output /tmp/imgcache \\
        --limit 100 \\
        --registry .image_path_registry.json

Features:
    - JIT caching with configurable TTL
    - Manifest-based path registry for fallback
    - Graceful handling of missing cache files
    - Progress tracking and statistics
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from io_utils.image_source import S3ImageSource
from io_utils.jit_cache import JITImageCache
from io_utils.path_registry import ImagePathRegistry
from io_utils.cached_source import CachedImageSource

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_image_hashes(manifest_path: Path) -> List[str]:
    """
    Load list of image SHA256 hashes from manifest or S3 listing.

    Args:
        manifest_path: Path to manifest file with image hashes

    Returns:
        List of SHA256 hashes
    """
    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        return []

    with open(manifest_path) as f:
        data = json.load(f)

    # Handle different manifest formats
    if "images" in data:
        return [img.get("sha256_hash") or img.get("hash") for img in data["images"]]
    elif isinstance(data, list):
        return data  # Assume list of hashes
    else:
        logger.error(f"Unknown manifest format: {manifest_path}")
        return []


def prepare_images(
    source: CachedImageSource,
    image_hashes: List[str],
    output_dir: Path,
    max_workers: int = 4,
) -> dict:
    """
    Download and cache images with progress tracking.

    Args:
        source: Cached image source
        image_hashes: List of SHA256 hashes to download
        output_dir: Output directory for images
        max_workers: Number of parallel downloads

    Returns:
        Statistics dictionary
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from tqdm import tqdm

    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {"total": len(image_hashes), "downloaded": 0, "cached": 0, "failed": 0}

    def download_image(sha_hash: str) -> tuple:
        """Download single image."""
        try:
            # Check if already cached
            cached_path = source.cache.get(sha_hash)
            if cached_path:
                stats["cached"] += 1
                return sha_hash, "cached", None

            # Download and cache
            image_path = source.get_image_path(sha_hash, download=True)
            if image_path:
                stats["downloaded"] += 1
                return sha_hash, "downloaded", None
            else:
                stats["failed"] += 1
                return sha_hash, "failed", "download_failed"

        except Exception as e:
            stats["failed"] += 1
            return sha_hash, "failed", str(e)

    logger.info(f"Preparing {len(image_hashes)} images with {max_workers} workers...")

    # Download images in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_image, sha_hash): sha_hash for sha_hash in image_hashes}

        with tqdm(total=len(image_hashes), desc="Downloading") as pbar:
            for future in as_completed(futures):
                sha_hash, status, error = future.result()
                pbar.update(1)

                if error:
                    logger.error(f"Failed: {sha_hash[:16]}... - {error}")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Prepare images for extraction with robust caching"
    )
    parser.add_argument("--bucket", type=str, required=True, help="S3 bucket name")
    parser.add_argument("--region", type=str, default="ca-central-1", help="AWS region")
    parser.add_argument(
        "--output", type=Path, default=Path("/tmp/imgcache"), help="Output cache directory"
    )
    parser.add_argument("--manifest", type=Path, help="Manifest file with image hashes")
    parser.add_argument("--limit", type=int, help="Limit number of images")
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path(".image_path_registry.json"),
        help="Path registry file",
    )
    parser.add_argument(
        "--ttl", type=int, default=14400, help="Cache TTL in seconds (default: 4 hours)"
    )
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel downloads")

    args = parser.parse_args()

    print("=" * 70)
    print("IMAGE PREPARATION WITH ROBUST CACHING")
    print("=" * 70)
    print(f"Bucket: s3://{args.bucket}")
    print(f"Region: {args.region}")
    print(f"Cache: {args.output}")
    print(f"Registry: {args.registry}")
    print(f"TTL: {args.ttl}s ({args.ttl / 3600:.1f}h)")
    print()

    # Initialize components
    logger.info("Initializing cache and registry...")

    # Create S3 source
    s3_source = S3ImageSource(bucket=args.bucket, region=args.region)

    # Create JIT cache
    cache = JITImageCache(
        cache_dir=args.output,
        default_ttl_seconds=args.ttl,
        auto_cleanup=True,
    )

    # Create path registry
    registry = ImagePathRegistry(args.registry)

    # Create cached source
    cached_source = CachedImageSource(
        source=s3_source,
        cache=cache,
        registry=registry,
        source_name=f"s3://{args.bucket}",
    )

    # Load image hashes
    if args.manifest:
        logger.info(f"Loading hashes from manifest: {args.manifest}")
        image_hashes = load_image_hashes(args.manifest)
    else:
        logger.error("--manifest is required (list of image hashes)")
        sys.exit(1)

    if not image_hashes:
        logger.error("No image hashes found")
        sys.exit(1)

    # Apply limit
    if args.limit:
        image_hashes = image_hashes[: args.limit]

    logger.info(f"Found {len(image_hashes)} images to prepare")

    # Prepare images
    stats = prepare_images(cached_source, image_hashes, args.output, max_workers=args.workers)

    # Save manifest for this run
    run_manifest_path = args.output / "image_manifest.json"
    manifest_data = {
        "manifest_id": args.output.name,
        "created_at": Path(__file__).stat().st_mtime,
        "source_bucket": args.bucket,
        "image_count": len(image_hashes),
        "images": [
            {
                "sha256_hash": sha_hash,
                "locations": [
                    {
                        "type": "s3",
                        "path": f"s3://{args.bucket}/images/{sha_hash[:2]}/{sha_hash[2:4]}/{sha_hash}.jpg",
                    },
                    {
                        "type": "cache",
                        "path": str(args.output / sha_hash[:2] / sha_hash[:4] / f"{sha_hash}.jpg"),
                    },
                ],
            }
            for sha_hash in image_hashes
        ],
    }

    with open(run_manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=2)

    logger.info(f"Saved manifest: {run_manifest_path}")

    # Print summary
    print()
    print("=" * 70)
    print("PREPARATION COMPLETE")
    print("=" * 70)
    print(f"Total images: {stats['total']}")
    print(f"Downloaded: {stats['downloaded']}")
    print(f"Already cached: {stats['cached']}")
    print(f"Failed: {stats['failed']}")
    print()

    # Cache statistics
    cache_stats = cached_source.get_stats()
    print("Cache Statistics:")
    print(f"  Hit rate: {cache_stats['hit_rate']:.1f}%")
    print(f"  Cached files: {cache_stats['entries']}")
    print(f"  Total size: {cache_stats['total_size_mb']:.1f} MB")
    print()

    # Registry statistics
    if registry:
        registry_stats = registry.get_stats()
        print("Registry Statistics:")
        print(f"  Total images: {registry_stats['total_images']}")
        print(f"  Total locations: {registry_stats['total_locations']}")
        print(f"  Location types: {registry_stats['location_types']}")
        print()

    print("✅ Images prepared and ready for extraction!")
    print(f"📂 Cache directory: {args.output}")
    print(f"📋 Manifest: {run_manifest_path}")
    print()

    if stats["failed"] > 0:
        print(f"⚠️  {stats['failed']} images failed to download")
        sys.exit(1)


if __name__ == "__main__":
    main()
