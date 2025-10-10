#!/usr/bin/env python3
"""Fetch images from S3 manifest and process with AAFC herbarium pipeline.

This script integrates the s3-image-dataset-kit with the AAFC OCR pipeline,
fetching images on-demand and tracking provenance.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
import getpass

# TODO: Eventually move s3-image-dataset-kit into this codebase as a module
# For now, add it to path
S3_KIT_PATH = Path.home() / "Documents/GitHub/s3-image-dataset-kit/src"
sys.path.insert(0, str(S3_KIT_PATH))

from dataset_tool.client import fetch_entry
from dataset_tool.config import SETTINGS


def read_manifest(manifest_path: Path) -> Iterator[dict]:
    """Read JSONL manifest and yield image entries."""
    with open(manifest_path) as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def fetch_images_to_cache(manifest_path: Path, cache_dir: Path) -> tuple[int, int]:
    """Fetch all images from manifest to local cache.

    Returns:
        (total_count, fetched_count) tuple
    """
    cache_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    fetched = 0

    print(f"📥 Fetching images from S3 to {cache_dir}")

    for entry in read_manifest(manifest_path):
        sha256 = entry["sha256"]
        total += 1

        # TODO(human): Implement fetch strategy and lineage tracking
        # Fetch options:
        # 1. Fetch all upfront (simple, predictable, uses disk space)
        # 2. Fetch on-demand during processing (complex, memory-efficient)
        # 3. Fetch in batches (compromise - fetch N, process N, repeat)
        #
        # Current implementation: Fetch all upfront
        # Benefit: CLI can run normally, clear separation of concerns
        # Tradeoff: ~300MB disk usage for 2,885 images
        #
        # Lineage tracking TODO:
        # - Link resized images (SHA256 hashes) back to original camera files
        # - Original files: ~/Documents/projects/AAFC/pyproj/resized/DSC_*.JPG
        # - Resized for GPT-4o testing, now in S3 with content-addressed naming
        # - Need mapping: original_filename → sha256_hash → processing_results
        # - Consider: Should this be in manifest metadata or separate lineage file?

        # Use s3-kit's fetch_entry - it handles caching automatically
        cached_path = fetch_entry(entry)

        if cached_path.exists():
            # Copy to flat cache directory for CLI
            flat_cache_path = cache_dir / f"{sha256}.jpg"
            if not flat_cache_path.exists():
                import shutil

                shutil.copy2(cached_path, flat_cache_path)
                fetched += 1
                if fetched % 100 == 0:
                    print(f"  Fetched {fetched}/{total} images...")
        else:
            print(f"  ⚠️ Failed to fetch: {sha256[:16]}...")

    print(f"✅ Fetch complete: {fetched} new, {total - fetched} already cached")

    # Clean up s3-kit's hierarchical cache to avoid duplicate processing
    # (iter_images uses rglob which would find files in both locations)
    print("🧹 Cleaning up hierarchical cache subdirectories...")
    import shutil

    for subdir in cache_dir.iterdir():
        if subdir.is_dir():
            shutil.rmtree(subdir)

    return total, fetched


def log_provenance(output_dir: Path, manifest_path: Path, cache_dir: Path):
    """Log basic provenance information for this processing run.

    Future enhancement: Comprehensive provenance tracking (#TODO: file issue)
    - Track original camera files → resized versions → processed results
    - Link to manual resize operations done for GPT-4o testing
    - Record transformation history (original → resize → S3 upload → processing)
    """
    provenance = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": getpass.getuser(),
        "hostname": os.uname().nodename,
        "source_bucket": SETTINGS.bucket,
        "source_manifest": str(manifest_path),
        "cache_directory": str(cache_dir),
        "aws_region": SETTINGS.region,
        "manifest_version": "v1",  # TODO: extract from manifest metadata
        "processing_version": "aafc-herbarium-0.3.0",
        "notes": {
            "image_preparation": "Images manually resized for GPT-4o testing",
            "original_source": "Camera files (DSC_*.JPG format)",
            "lineage_tracking": "TODO: Link resized SHA256 hashes to original filenames",
            "future_work": "See GitHub issue for comprehensive provenance system",
        },
    }

    provenance_file = output_dir / "provenance.json"
    with open(provenance_file, "w") as f:
        json.dump(provenance, f, indent=2)

    print(f"📝 Provenance logged to {provenance_file}")
    print("   Note: Original→resized lineage tracking pending (see provenance.json)")


def run_processing(cache_dir: Path, output_dir: Path, engine: str = "vision"):
    """Run the AAFC herbarium CLI on cached images."""
    print(f"\n🔬 Starting OCR processing with {engine}")
    print(f"   Input: {cache_dir}")
    print(f"   Output: {output_dir}")
    print("   Estimated time: ~3.3 hours for 2,885 specimens\n")

    cmd = [
        "python",
        "cli.py",
        "process",
        "--input",
        str(cache_dir),
        "--output",
        str(output_dir),
        "--engine",
        engine,
    ]

    subprocess.run(cmd, check=True)


def main():
    # Configuration
    manifest_path = (
        Path.home() / "Documents/GitHub/s3-image-dataset-kit/manifests/inventory-v1.jsonl"
    )
    cache_dir = Path("/tmp/imgcache")  # From .env CACHE_DIR
    output_dir = Path("full_dataset_processing") / f"run_{datetime.now():%Y%m%d_%H%M%S}"

    print("=" * 80)
    print("AAFC Herbarium Full Dataset Processing with S3 Integration")
    print("=" * 80)
    print(f"Manifest: {manifest_path}")
    print(f"Cache: {cache_dir}")
    print(f"Output: {output_dir}\n")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Log provenance first
    log_provenance(output_dir, manifest_path, cache_dir)

    # Fetch images
    total, fetched = fetch_images_to_cache(manifest_path, cache_dir)
    print(f"\n📊 Total images: {total}")

    # Run processing
    run_processing(cache_dir, output_dir, engine="vision")

    print("\n" + "=" * 80)
    print("✅ Processing complete!")
    print(f"Results: {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
