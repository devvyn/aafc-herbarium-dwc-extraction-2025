#!/usr/bin/env python3
"""Analyze spatial zones in herbarium specimen images.

This script processes specimen images using Vision OCR to extract bounding boxes,
then creates spatial zone templates mapping text locations to coarse 9-zone grids.

Usage:
    # Analyze a small sample (default: 10 specimens)
    uv run python scripts/analyze_spatial_zones.py

    # Analyze specific number of specimens
    uv run python scripts/analyze_spatial_zones.py --limit 50

    # Analyze all specimens (long running!)
    uv run python scripts/analyze_spatial_zones.py --all

    # Process specific specimen
    uv run python scripts/analyze_spatial_zones.py --specimen-id abc123...

Output:
    - deliverables/v1.0_vision_baseline/spatial_zones.jsonl
    - Zone distribution statistics printed to console
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

# Add project dirs to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

from engines.vision_swift.run import run as vision_ocr  # noqa: E402
from spatial.zone_detector import create_template, get_zone_statistics, SpatialTemplate  # noqa: E402


def get_image_cache_path(specimen_id: str, base_dir: Path) -> Path | None:
    """Find cached image for specimen ID.

    Parameters
    ----------
    specimen_id : str
        Specimen SHA256 hash
    base_dir : Path
        Base directory containing images (e.g., deliverables/v1.0_vision_baseline)

    Returns
    -------
    Path or None
        Path to image file if found
    """
    # Check deliverables directory
    img_path = base_dir / f"{specimen_id}.jpg"
    if img_path.exists():
        return img_path

    # Check common cache locations
    cache_dirs = [
        Path("/tmp/imgcache"),
        Path.home() / ".cache" / "herbarium_dwc" / "images",
    ]

    for cache_dir in cache_dirs:
        if not cache_dir.exists():
            continue

        # Content-addressed storage with nested subdirectories: imgcache/00/0e/000e...jpg
        prefix1 = specimen_id[:2]
        prefix2 = specimen_id[2:4]
        img_path = cache_dir / prefix1 / prefix2 / f"{specimen_id}.jpg"
        if img_path.exists():
            return img_path

        # Also try single subdir: imgcache/00/000e...jpg
        img_path = cache_dir / prefix1 / f"{specimen_id}.jpg"
        if img_path.exists():
            return img_path

        # Also try flat structure
        img_path = cache_dir / f"{specimen_id}.jpg"
        if img_path.exists():
            return img_path

    return None


def process_specimen(specimen_id: str, image_path: Path) -> SpatialTemplate | None:
    """Process a single specimen to extract spatial zones.

    Parameters
    ----------
    specimen_id : str
        Specimen identifier
    image_path : Path
        Path to specimen image

    Returns
    -------
    SpatialTemplate or None
        Spatial template if successful, None on error
    """
    try:
        print(f"Processing {specimen_id[:16]}...", end=" ", flush=True)

        # Run Vision OCR
        tokens, boxes, confidences = vision_ocr(str(image_path))

        if not tokens:
            print("no text detected")
            return None

        # Create spatial template
        template = create_template(specimen_id, tokens, boxes, confidences)

        print(
            f"OK ({len(tokens)} text blocks, {len(set(str(z) for z in template.zones_by_text.values()))} unique zones)"
        )
        return template

    except Exception as e:
        print(f"ERROR: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Analyze spatial zones in specimen images")
    parser.add_argument(
        "--extraction-dir",
        type=Path,
        default=Path("deliverables/v1.0_vision_baseline"),
        help="Extraction directory containing raw.jsonl",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of specimens to analyze (default: 10)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Analyze all specimens (overrides --limit)",
    )
    parser.add_argument(
        "--specimen-id",
        type=str,
        help="Process specific specimen ID only",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path (default: extraction_dir/spatial_zones.jsonl)",
    )

    args = parser.parse_args()

    extraction_dir = args.extraction_dir.resolve()
    if not extraction_dir.exists():
        print(f"Error: Extraction directory not found: {extraction_dir}")
        return 1

    raw_file = extraction_dir / "raw.jsonl"
    if not raw_file.exists():
        print(f"Error: raw.jsonl not found: {raw_file}")
        return 1

    # Determine output path
    output_path = args.output if args.output else extraction_dir / "spatial_zones.jsonl"

    print("=" * 70)
    print("SPATIAL ZONE ANALYSIS")
    print("=" * 70)
    print(f"Extraction directory: {extraction_dir}")
    print(f"Output: {output_path}")
    print()

    # Load specimen IDs from raw.jsonl
    specimen_ids: List[str] = []
    if args.specimen_id:
        specimen_ids = [args.specimen_id]
        print(f"Processing specific specimen: {args.specimen_id[:16]}...")
    else:
        with open(raw_file) as f:
            for line in f:
                record = json.loads(line)
                specimen_ids.append(record["specimen_id"])

        if not args.all:
            specimen_ids = specimen_ids[: args.limit]

        print(f"Found {len(specimen_ids)} specimens to process")

    print()

    # Process specimens
    templates: List[SpatialTemplate] = []
    processed = 0
    failed = 0

    for specimen_id in specimen_ids:
        # Find image file
        image_path = get_image_cache_path(specimen_id, extraction_dir)
        if not image_path:
            print(f"Warning: Image not found for {specimen_id[:16]}, skipping")
            failed += 1
            continue

        # Process specimen
        template = process_specimen(specimen_id, image_path)
        if template:
            templates.append(template)
            processed += 1
        else:
            failed += 1

    print()
    print("=" * 70)
    print(f"Processed: {processed} specimens")
    print(f"Failed: {failed} specimens")
    print()

    if not templates:
        print("No templates generated. Exiting.")
        return 1

    # Calculate statistics
    stats = get_zone_statistics(templates)
    print("Zone Distribution:")
    print("-" * 40)
    for zone, count in sorted(stats["zone_distribution"].items(), key=lambda x: -x[1]):
        pct = 100 * count / sum(stats["zone_distribution"].values())
        print(f"  {zone:20s} {count:6d} ({pct:5.1f}%)")

    # Write output
    print()
    print(f"Writing templates to {output_path}...")
    with open(output_path, "w") as f:
        for template in templates:
            f.write(json.dumps(template.to_dict()) + "\n")

    print(f"Done! {len(templates)} templates written.")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
