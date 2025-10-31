#!/usr/bin/env python3
"""
Manually publish latest data to docs/data-latest/ for continuous access.

This script does locally what the GitHub Action does automatically.
Use this to test publishing before pushing to main.
"""

from pathlib import Path
from dwc.archive import create_archive
import shutil
from datetime import datetime, timezone
import json
import sys


def find_latest_data():
    """Find the most recent occurrence.csv in deliverables/."""
    deliverables = Path("deliverables")
    csv_files = list(deliverables.glob("**/occurrence.csv"))

    if not csv_files:
        print("❌ No occurrence.csv found in deliverables/")
        return None, None

    # Use most recently modified
    latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
    latest_jsonl = latest_csv.parent / "raw.jsonl"

    return latest_csv, latest_jsonl if latest_jsonl.exists() else None


def publish_continuous():
    """Publish latest data to docs/data-latest/."""

    print("=" * 70)
    print("CONTINUOUS DATA PUBLISHING")
    print("=" * 70)

    # Find latest data
    csv_path, jsonl_path = find_latest_data()
    if not csv_path:
        return 1

    print(f"📄 CSV:  {csv_path}")
    if jsonl_path:
        print(f"📋 JSONL: {jsonl_path}")
    print()

    # Create staging
    staging = Path("docs/data-staging")
    staging.mkdir(exist_ok=True)

    print("🔄 Generating Darwin Core Archive...")
    shutil.copy(csv_path, staging / "occurrence.csv")

    # Count records
    record_count = sum(1 for _ in open(csv_path)) - 1

    # Generate archive
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    archive_path = create_archive(
        staging,
        compress=True,
        version="0.0.0-dev",
        filters={"build": timestamp, "type": "continuous"},
        bundle_format="simple",
        include_checksums=True,
    )

    # Prepare output
    output = Path("docs/data-latest")
    output.mkdir(exist_ok=True, parents=True)

    # Copy files
    print("📦 Publishing to docs/data-latest/...")
    shutil.copy(csv_path, output / "occurrence.csv")
    shutil.move(str(archive_path), str(output / "dwc-archive.zip"))

    if jsonl_path:
        shutil.copy(jsonl_path, output / "raw.jsonl")

    # Write metadata
    metadata = {
        "timestamp": timestamp,
        "timestamp_iso": datetime.now(timezone.utc).isoformat(),
        "source_csv": str(csv_path),
        "record_count": record_count,
        "build_type": "continuous",
        "branch": "local",
        "files": {
            "occurrence.csv": {
                "size_kb": (output / "occurrence.csv").stat().st_size / 1024,
                "format": "Darwin Core CSV",
            },
            "dwc-archive.zip": {
                "size_kb": (output / "dwc-archive.zip").stat().st_size / 1024,
                "format": "Darwin Core Archive (GBIF)",
            },
        },
    }

    if jsonl_path:
        metadata["files"]["raw.jsonl"] = {
            "size_mb": (output / "raw.jsonl").stat().st_size / (1024 * 1024),
            "format": "JSONL with confidence scores",
        }

    with open(output / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print()
    print("✅ Published successfully!")
    print()
    print("📊 Summary:")
    print(f"   Records: {record_count}")
    print(f"   CSV: {metadata['files']['occurrence.csv']['size_kb']:.1f} KB")
    print(f"   Archive: {metadata['files']['dwc-archive.zip']['size_kb']:.1f} KB")
    if "raw.jsonl" in metadata["files"]:
        print(f"   JSONL: {metadata['files']['raw.jsonl']['size_mb']:.1f} MB")
    print()
    print(f"📁 Output: {output}")
    print()
    print("🌐 After committing and pushing:")
    print("   https://devvyn.github.io/aafc-herbarium-dwc-extraction-2025/data-latest/")

    return 0


if __name__ == "__main__":
    sys.exit(publish_continuous())
