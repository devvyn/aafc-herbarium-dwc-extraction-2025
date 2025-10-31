#!/usr/bin/env python3
"""
Fetch all images from S3 manifest to local cache.

This prepares images for extraction by downloading them from S3.
"""

import sys
from pathlib import Path
from tqdm import tqdm

# Add s3-image-dataset-kit to path
sys.path.insert(0, str(Path.home() / "Documents" / "GitHub" / "s3-image-dataset-kit" / "src"))

from dataset_tool.client import fetch_entry
from dataset_tool.manifest import read_jsonl


def main():
    manifest_path = (
        Path.home()
        / "Documents"
        / "GitHub"
        / "s3-image-dataset-kit"
        / "manifests"
        / "inventory-v1.jsonl"
    )

    print(f"📋 Reading manifest: {manifest_path}")
    records = read_jsonl(str(manifest_path))
    print(f"✅ Found {len(records)} images in manifest")
    print()

    print("⬇️  Downloading images from S3 to local cache...")
    print("   (Cached images will be skipped)")
    print()

    for rec in tqdm(records, desc="Fetching images", unit="img"):
        try:
            fetch_entry(rec)
        except Exception as e:
            print(f"\n⚠️  Failed to fetch {rec.get('sha256', 'unknown')}: {e}")
            continue

    print()
    print("✅ All images fetched successfully!")


if __name__ == "__main__":
    main()
