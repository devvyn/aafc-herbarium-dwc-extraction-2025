#!/usr/bin/env python3
"""Example: Scientific provenance tracking for herbarium workflows.

Demonstrates best practices for capturing version metadata in
scientific data processing pipelines.

Usage:
    python examples/provenance_example.py
"""

import json
from datetime import datetime, timezone
from pathlib import Path

# Import provenance utilities
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from provenance import (
    capture_git_provenance,
    capture_system_info,
    create_manifest,
    save_manifest,
    validate_reproducibility,
    track_provenance,
)


# Example 1: Basic provenance capture
def example_basic_capture():
    """Basic example: Capture git provenance at processing start."""
    print("=== Example 1: Basic Provenance Capture ===\n")

    # Capture at processing start
    git_info = capture_git_provenance()

    print("Git Provenance:")
    print(f"  Commit: {git_info.get('git_commit', 'unknown')[:7]}")
    print(f"  Branch: {git_info.get('git_branch', 'unknown')}")
    print(f"  Dirty:  {git_info.get('git_dirty', False)}")

    # Warn if dirty
    if git_info.get("git_dirty"):
        print("\n⚠️  Warning: Uncommitted changes detected!")
        print("   Consider committing before processing for reproducibility.")
    else:
        print("\n✅ Clean working tree - reproducible state")

    return git_info


# Example 2: Create export manifest
def example_export_manifest():
    """Example: Create manifest for scientific data export."""
    print("\n=== Example 2: Export Manifest ===\n")

    # Process data (simulated)
    specimen_count = 2885
    processing_start = datetime.now(timezone.utc)

    # ... do processing ...

    processing_end = datetime.now(timezone.utc)
    duration = (processing_end - processing_start).total_seconds()

    # Create manifest with provenance
    manifest = create_manifest(
        version="1.0.0",
        custom_metadata={
            "export_type": "Darwin Core Archive",
            "specimen_count": specimen_count,
            "processing": {
                "start": processing_start.isoformat(),
                "end": processing_end.isoformat(),
                "duration_seconds": duration,
                "errors": 0,
            },
        }
    )

    print("Export Manifest:")
    print(json.dumps(manifest, indent=2))

    # Save to file
    output_dir = Path("test_output")
    save_manifest(manifest, output_dir / "manifest.json")

    return manifest


# Example 3: Using decorator for automatic tracking
@track_provenance(version="1.0.0")
def process_specimens_with_tracking(input_dir: Path, output_dir: Path):
    """Process specimens with automatic provenance tracking.

    The @track_provenance decorator captures git info at function entry.
    """
    print("\n=== Example 3: Automatic Tracking (Decorator) ===\n")

    # Git info automatically captured and attached
    print(f"Processing with commit: {process_specimens_with_tracking.git_info['git_commit'][:7]}")

    # ... do processing ...

    # Create manifest using captured info
    manifest = create_manifest(
        version="1.0.0",
        git_info=process_specimens_with_tracking.git_info,
        system_info=process_specimens_with_tracking.system_info,
        custom_metadata={
            "input_dir": str(input_dir),
            "output_dir": str(output_dir),
            "specimen_count": 42,
        }
    )

    save_manifest(manifest, output_dir / "manifest.json")
    return manifest


# Example 4: Validation for reproducibility
def example_validate_reproducibility():
    """Example: Validate environment matches manifest for reproducibility."""
    print("\n=== Example 4: Reproducibility Validation ===\n")

    manifest_path = Path("test_output/manifest.json")

    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}")
        return

    is_valid, warnings = validate_reproducibility(manifest_path)

    if is_valid:
        print("✅ Environment matches manifest - reproducible!")
    else:
        print("⚠️  Environment mismatch detected:")
        for warning in warnings:
            print(f"   - {warning}")

    return is_valid, warnings


# Example 5: Fragment accumulation pattern (evolution to Content DAG)
def example_fragment_accumulation():
    """Example: Evolving to Content DAG for metadata fragments.

    Shows how git provenance can be enhanced with content addressing
    for long-term metadata accumulation.
    """
    print("\n=== Example 5: Fragment Accumulation Pattern ===\n")

    # Specimen collected in 1987
    field_notes = {
        "collector": "J. Smith",
        "date": "1987-06-15",
        "git_commit": "abc123",  # Original processing
        "timestamp": "1987-06-15T10:00:00Z"
    }

    # Georeference corrected in 2023
    georef_correction = {
        "lat": 45.123,
        "lon": -75.456,
        "corrected_date": "2023-05-10",
        "git_commit": "def456",  # Different codebase!
        "timestamp": "2023-05-10T14:30:00Z"
    }

    # Taxonomic update in 2024
    taxonomy_update = {
        "species": "Carex updated",
        "determiner": "Dr. Lee",
        "determination_date": "2024-08-20",
        "git_commit": "ghi789",  # Another codebase
        "timestamp": "2024-08-20T09:15:00Z"
    }

    print("Fragment History (git provenance per fragment):")
    print(f"  1987: Field collection (commit: {field_notes['git_commit']})")
    print(f"  2023: Georeference (commit: {georef_correction['git_commit']})")
    print(f"  2024: Taxonomy update (commit: {taxonomy_update['git_commit']})")

    print("\nCurrent state: All fragments preserved with provenance")
    print("Can query: 'What did we know in 2020?' → field_notes + georef_correction")

    # This pattern naturally evolves to Content DAG
    # See: ~/devvyn-meta-project/docs/CONTENT_DAG_PATTERN.md
    print("\n💡 Evolution: Content DAG pattern handles this more elegantly")
    print("   - Each fragment gets content hash")
    print("   - Explicit DAG links between fragments")
    print("   - Works across repos/systems")
    print("   - Git commits still captured (belt-and-suspenders)")


# Run examples
if __name__ == "__main__":
    print("Scientific Provenance Pattern - Examples")
    print("=" * 60)

    # Run all examples
    git_info = example_basic_capture()
    manifest = example_export_manifest()

    # Decorator example
    test_input = Path("test_input")
    test_output = Path("test_output")
    test_input.mkdir(exist_ok=True)
    test_output.mkdir(exist_ok=True)

    manifest_with_tracking = process_specimens_with_tracking(test_input, test_output)

    # Validation
    is_valid, warnings = example_validate_reproducibility()

    # Fragment accumulation
    example_fragment_accumulation()

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("\nNext steps:")
    print("  1. Review generated manifest: test_output/manifest.json")
    print("  2. Read pattern doc: docs/SCIENTIFIC_PROVENANCE_PATTERN.md")
    print("  3. Explore Content DAG: ~/devvyn-meta-project/docs/CONTENT_DAG_PATTERN.md")
