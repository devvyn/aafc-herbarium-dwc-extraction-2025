#!/usr/bin/env python3
"""Content DAG integration for herbarium metadata fragments.

Demonstrates evolving from git-based provenance to content-addressed DAG
for herbarium specimen metadata that accumulates over decades.

Key Insight: Specimen metadata is NOT immutable - it accumulates!
- 1987: Field collection notes
- 2010: Digitization (image capture)
- 2023: Georeference correction
- 2024: Taxonomic redetermination
- 2025: AI-extracted Darwin Core terms

Each fragment should preserve its provenance (git commit, timestamp, author)
while being content-addressable for deduplication and forensic queries.

Usage:
    python examples/content_dag_herbarium.py
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# Simplified Content DAG primitives (see meta-project for full implementation)
def hash_content(content: str | bytes) -> str:
    """Hash content using SHA256.

    Args:
        content: String or bytes to hash

    Returns:
        SHA256 hex digest
    """
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def create_dag_node(
    content_hash: str, inputs: list[str], metadata: dict, timestamp: Optional[str] = None
) -> dict:
    """Create DAG node linking content to inputs.

    Args:
        content_hash: SHA256 hash of this node's content
        inputs: List of input content hashes (empty for root nodes)
        metadata: Domain-specific metadata (git_commit, type, author, etc.)
        timestamp: ISO timestamp (auto-generated if None)

    Returns:
        DAG node dict
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()

    return {
        "hash": content_hash,
        "inputs": inputs,
        "metadata": metadata,
        "timestamp": timestamp,
    }


def store_dag_node(node: dict, output_dir: Path) -> Path:
    """Store DAG node to filesystem.

    Args:
        node: DAG node from create_dag_node()
        output_dir: Directory for DAG nodes

    Returns:
        Path to stored node file
    """
    dag_dir = output_dir / "dag" / "nodes"
    dag_dir.mkdir(parents=True, exist_ok=True)

    # Store by content hash
    node_path = dag_dir / f"{node['hash'][:16]}.json"
    with open(node_path, "w") as f:
        json.dump(node, f, indent=2)

    return node_path


# Example: Herbarium specimen metadata accumulation
def example_specimen_lifecycle():
    """Demonstrate metadata fragment accumulation over decades."""
    print("=== Herbarium Specimen Metadata Lifecycle ===\n")

    output_dir = Path("test_output/dag_example")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1987: Field collection (root node)
    field_notes = {
        "specimen_id": "AAFC-12345",
        "collector": "J. Smith",
        "collection_date": "1987-06-15",
        "locality": "Near Saskatoon",
        "notes": "Collected from roadside",
    }
    field_notes_json = json.dumps(field_notes, sort_keys=True)
    field_notes_hash = hash_content(field_notes_json)

    field_notes_node = create_dag_node(
        content_hash=field_notes_hash,
        inputs=[],  # Root node
        metadata={
            "type": "field_collection",
            "git_commit": "abc123",  # Original digitization code
            "author": "J. Smith",
        },
        timestamp="1987-06-15T10:00:00Z",
    )
    store_dag_node(field_notes_node, output_dir)

    print("1987: Field collection")
    print(f"  Hash: {field_notes_hash[:16]}")
    print(f"  Collector: {field_notes['collector']}")
    print()

    # 2010: Digitization (image capture)
    # Simulate image hash (in real workflow, hash actual image file)
    image_content = b"<simulated image bytes>"
    image_hash = hash_content(image_content)

    digitization_metadata = {
        "specimen_id": "AAFC-12345",
        "image_filename": "AAFC-12345.jpg",
        "scanner": "Canon EOS 5D",
        "resolution_dpi": 600,
        "digitizer": "M. Johnson",
    }
    digitization_json = json.dumps(digitization_metadata, sort_keys=True)
    digitization_hash = hash_content(digitization_json)

    digitization_node = create_dag_node(
        content_hash=digitization_hash,
        inputs=[field_notes_hash],  # Links to field notes
        metadata={
            "type": "digitization",
            "git_commit": "def456",  # Digitization workflow code
            "author": "M. Johnson",
            "image_hash": image_hash,  # Link to actual image
        },
        timestamp="2010-03-20T14:30:00Z",
    )
    store_dag_node(digitization_node, output_dir)

    print("2010: Digitization")
    print(f"  Hash: {digitization_hash[:16]}")
    print(f"  Image: {image_hash[:16]}")
    print(f"  Inputs: {field_notes_hash[:16]}")
    print()

    # 2023: Georeference correction
    georeference = {
        "specimen_id": "AAFC-12345",
        "decimal_latitude": 52.1332,
        "decimal_longitude": -106.6700,
        "coordinate_uncertainty_meters": 1000,
        "georeference_notes": "Corrected using Google Maps",
        "georeferenced_by": "Dr. A. Lee",
    }
    georeference_json = json.dumps(georeference, sort_keys=True)
    georeference_hash = hash_content(georeference_json)

    georeference_node = create_dag_node(
        content_hash=georeference_hash,
        inputs=[field_notes_hash],  # Links to original locality info
        metadata={
            "type": "georeference_correction",
            "git_commit": "ghi789",  # Georeferencing tool code
            "author": "Dr. A. Lee",
        },
        timestamp="2023-05-10T09:15:00Z",
    )
    store_dag_node(georeference_node, output_dir)

    print("2023: Georeference correction")
    print(f"  Hash: {georeference_hash[:16]}")
    print(
        f"  Coordinates: ({georeference['decimal_latitude']}, {georeference['decimal_longitude']})"
    )
    print(f"  Inputs: {field_notes_hash[:16]}")
    print()

    # 2024: Taxonomic redetermination
    taxonomy = {
        "specimen_id": "AAFC-12345",
        "scientific_name": "Carex praegracilis W. Boott",
        "family": "Cyperaceae",
        "identified_by": "Dr. P. Singh",
        "identification_date": "2024-08-20",
        "identification_notes": "Redetermined from C. siccata",
    }
    taxonomy_json = json.dumps(taxonomy, sort_keys=True)
    taxonomy_hash = hash_content(taxonomy_json)

    taxonomy_node = create_dag_node(
        content_hash=taxonomy_hash,
        inputs=[field_notes_hash],  # Original specimen
        metadata={
            "type": "taxonomic_determination",
            "git_commit": "jkl012",  # Taxonomy database code
            "author": "Dr. P. Singh",
        },
        timestamp="2024-08-20T11:45:00Z",
    )
    store_dag_node(taxonomy_node, output_dir)

    print("2024: Taxonomic redetermination")
    print(f"  Hash: {taxonomy_hash[:16]}")
    print(f"  Scientific name: {taxonomy['scientific_name']}")
    print(f"  Inputs: {field_notes_hash[:16]}")
    print()

    # 2025: AI-extracted Darwin Core terms (from image)
    ai_extraction = {
        "specimen_id": "AAFC-12345",
        "catalog_number": "019121",
        "recorded_by": "J. Smith",
        "event_date": "1969-08-14",  # AI found different date on label!
        "locality": "Beaver River crossing",
        "state_province": "Saskatchewan",
        "country": "Canada",
        "extraction_confidence": 0.85,
    }
    ai_extraction_json = json.dumps(ai_extraction, sort_keys=True)
    ai_extraction_hash = hash_content(ai_extraction_json)

    ai_extraction_node = create_dag_node(
        content_hash=ai_extraction_hash,
        inputs=[image_hash],  # AI extracted from image
        metadata={
            "type": "ai_extraction",
            "git_commit": "mno345",  # This project's code!
            "model": "gpt-4o-mini",
            "extraction_version": "1.0.0",
        },
        timestamp="2025-10-08T16:20:00Z",
    )
    store_dag_node(ai_extraction_node, output_dir)

    print("2025: AI extraction from image")
    print(f"  Hash: {ai_extraction_hash[:16]}")
    print(f"  Event date: {ai_extraction['event_date']} (conflicts with field notes!)")
    print(f"  Inputs: {image_hash[:16]}")
    print()

    # Merged view: Combine all fragments
    merged_record = {
        **field_notes,
        **digitization_metadata,
        **georeference,
        **taxonomy,
        **ai_extraction,
    }
    merged_json = json.dumps(merged_record, sort_keys=True)
    merged_hash = hash_content(merged_json)

    merged_node = create_dag_node(
        content_hash=merged_hash,
        inputs=[
            field_notes_hash,
            digitization_hash,
            georeference_hash,
            taxonomy_hash,
            ai_extraction_hash,
        ],
        metadata={
            "type": "merged_specimen_record",
            "git_commit": "pqr678",
            "merge_strategy": "latest_wins",
        },
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    store_dag_node(merged_node, output_dir)

    print("2025: Merged record (all fragments)")
    print(f"  Hash: {merged_hash[:16]}")
    print(f"  Inputs: {len(merged_node['inputs'])} fragments")
    print()

    # Provenance queries
    print("=== Provenance Queries ===\n")

    # Query 1: What did we know in 2020?
    print("Query: 'What did we know about this specimen in 2020?'")
    print("  Answer: field_notes + digitization (before georeference)")
    print()

    # Query 2: Where did event_date come from?
    print("Query: 'Where did event_date=1969-08-14 come from?'")
    print("  Answer: AI extraction (2025), conflicts with field notes (1987)")
    print("  Resolution: Review image to verify")
    print()

    # Query 3: Has this specimen been updated?
    print("Query: 'Has taxonomy changed?'")
    print("  Answer: Yes, redetermined in 2024 from C. siccata to C. praegracilis")
    print()

    # Save DAG visualization
    dag_summary = {
        "specimen_id": "AAFC-12345",
        "fragments": {
            "field_collection": {
                "hash": field_notes_hash[:16],
                "timestamp": "1987-06-15",
                "git_commit": "abc123",
            },
            "digitization": {
                "hash": digitization_hash[:16],
                "timestamp": "2010-03-20",
                "git_commit": "def456",
            },
            "georeference": {
                "hash": georeference_hash[:16],
                "timestamp": "2023-05-10",
                "git_commit": "ghi789",
            },
            "taxonomy": {
                "hash": taxonomy_hash[:16],
                "timestamp": "2024-08-20",
                "git_commit": "jkl012",
            },
            "ai_extraction": {
                "hash": ai_extraction_hash[:16],
                "timestamp": "2025-10-08",
                "git_commit": "mno345",
            },
            "merged": {
                "hash": merged_hash[:16],
                "timestamp": datetime.now(timezone.utc).isoformat()[:19],
                "git_commit": "pqr678",
            },
        },
        "provenance_tree": f"""
{field_notes_hash[:8]} (1987) ─┬─> {digitization_hash[:8]} (2010) ──> {merged_hash[:8]} (2025)
                               ├─> {georeference_hash[:8]} (2023) ──> {merged_hash[:8]}
                               └─> {taxonomy_hash[:8]} (2024) ──────> {merged_hash[:8]}
        {image_hash[:8]} (2010) ──────> {ai_extraction_hash[:8]} (2025) ──> {merged_hash[:8]}
        """.strip(),
    }

    dag_summary_path = output_dir / "specimen_dag_summary.json"
    with open(dag_summary_path, "w") as f:
        json.dump(dag_summary, f, indent=2)

    print(f"DAG summary saved: {dag_summary_path}")
    print("\n" + dag_summary["provenance_tree"])


# Example: Deduplication using content hashing
def example_deduplication():
    """Demonstrate duplicate detection using content hashes."""
    print("\n\n=== Deduplication Example ===\n")

    # Scenario: Same specimen processed in two batches
    specimen_data = {
        "catalog_number": "019121",
        "scientific_name": "Bouteloua gracilis",
        "locality": "Saskatoon",
    }

    # Batch A
    batch_a_json = json.dumps(specimen_data, sort_keys=True)
    batch_a_hash = hash_content(batch_a_json)

    # Batch B (retry/duplicate)
    batch_b_json = json.dumps(specimen_data, sort_keys=True)
    batch_b_hash = hash_content(batch_b_json)

    print(f"Batch A hash: {batch_a_hash[:16]}")
    print(f"Batch B hash: {batch_b_hash[:16]}")

    if batch_a_hash == batch_b_hash:
        print("\n✅ Hashes match - duplicate detected!")
        print("   No need to process again, reference existing result")
    else:
        print("\n❌ Different content - process independently")


if __name__ == "__main__":
    print("Content DAG Integration for Herbarium Workflows")
    print("=" * 60)
    print()

    example_specimen_lifecycle()
    example_deduplication()

    print("\n" + "=" * 60)
    print("Content DAG demonstration complete!")
    print("\nKey Benefits:")
    print("  ✅ Every fragment preserves its git commit (provenance)")
    print("  ✅ Content-addressed (deduplication, identity)")
    print("  ✅ Explicit DAG links (forensic queries)")
    print("  ✅ Works across repos/decades (no git dependency)")
    print("\nNext steps:")
    print("  1. Review: test_output/dag_example/dag/nodes/")
    print("  2. Read: docs/SCIENTIFIC_PROVENANCE_PATTERN.md")
    print("  3. Explore: ~/devvyn-meta-project/docs/CONTENT_DAG_PATTERN.md")
    print("\nEvolution path:")
    print("  Git provenance (now) → Content DAG (future metadata accumulation)")
