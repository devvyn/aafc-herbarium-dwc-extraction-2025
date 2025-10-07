#!/usr/bin/env python
"""
Process OpenAI Batch API Results

Converts batch API output to standard extraction format.
Generates summary statistics and error reports.

Usage:
    python scripts/process_batch_results.py --input full_dataset_processing/gpt4omini_batch/batch_output.jsonl

    # With batch ID (will auto-download results first):
    python scripts/process_batch_results.py --batch-id batch_abc123
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def download_batch_results(batch_id: str, output_dir: Path) -> Path:
    """Download batch results if not already present.

    Args:
        batch_id: Batch job ID
        output_dir: Directory to save results

    Returns:
        Path to downloaded batch output file
    """
    if OpenAI is None:
        raise ImportError("OpenAI SDK not installed")

    client = OpenAI()

    print(f"📥 Downloading batch results for: {batch_id}")

    batch = client.batches.retrieve(batch_id)

    if batch.status != "completed":
        raise ValueError(f"Batch not complete (status: {batch.status})")

    if not batch.output_file_id:
        raise ValueError("No output file available")

    # Download
    output_path = output_dir / "batch_output.jsonl"

    content = client.files.content(batch.output_file_id)
    with open(output_path, "wb") as f:
        f.write(content.read())

    print(f"✅ Downloaded: {output_path}")

    return output_path


def parse_batch_response(response: Dict) -> Optional[Dict]:
    """Parse a single batch response into extraction format.

    Args:
        response: Batch response dict from OpenAI

    Returns:
        Extraction dict in standard format, or None if error
    """
    try:
        # Extract custom_id to get sha256
        custom_id = response["custom_id"]
        sha256 = custom_id.replace("specimen-", "")

        # Get response body
        if response.get("error"):
            return {
                "sha256": sha256,
                "custom_id": custom_id,
                "error": response["error"],
                "status": "failed"
            }

        body = response.get("response", {}).get("body", {})
        choices = body.get("choices", [])

        if not choices:
            return {
                "sha256": sha256,
                "custom_id": custom_id,
                "error": "No choices in response",
                "status": "failed"
            }

        # Parse content
        message = choices[0].get("message", {})
        content = message.get("content", "{}")

        # Parse JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return {
                "sha256": sha256,
                "custom_id": custom_id,
                "error": f"JSON parse error: {e}",
                "status": "failed",
                "raw_content": content
            }

        # Extract DWC fields and confidences
        dwc = {}
        dwc_confidence = {}

        # Check if this is OCR-first format with PASS_2 structure
        if "PASS_2" in data or "pass_2" in data or "PASS 2" in data:
            # Extract from PASS_2 nested structure
            pass_2_data = data.get("PASS_2") or data.get("pass_2") or data.get("PASS 2", {})
            for field, value in pass_2_data.items():
                if isinstance(value, dict):
                    dwc[field] = value.get("value", "")
                    dwc_confidence[field] = float(value.get("confidence", 0.0))
                elif isinstance(value, str):
                    dwc[field] = value
                    dwc_confidence[field] = 0.5
        else:
            # Standard format (few-shot, CoT)
            for field, value in data.items():
                if isinstance(value, dict):
                    dwc[field] = value.get("value", "")
                    dwc_confidence[field] = float(value.get("confidence", 0.0))
                elif isinstance(value, str):
                    # Fallback for non-structured response
                    dwc[field] = value
                    dwc_confidence[field] = 0.5  # Default confidence

        # Create extraction record
        extraction = {
            "run_id": f"batch-{datetime.now().isoformat()}",
            "image": f"{sha256}.jpg",
            "sha256": sha256,
            "engine": "gpt",
            "engine_version": "gpt-4o-mini",
            "dwc": dwc,
            "dwc_confidence": dwc_confidence,
            "flags": [],
            "added_fields": [],
            "errors": [],
            "batch_custom_id": custom_id,
            "batch_response_id": response.get("id"),
        }

        return extraction

    except Exception as e:
        return {
            "sha256": response.get("custom_id", "unknown").replace("specimen-", ""),
            "custom_id": response.get("custom_id"),
            "error": f"Processing error: {e}",
            "status": "failed"
        }


def generate_statistics(extractions: List[Dict]) -> Dict:
    """Generate summary statistics from extractions.

    Args:
        extractions: List of extraction dicts

    Returns:
        Statistics dict
    """
    total = len(extractions)
    successful = sum(1 for e in extractions if "error" not in e)
    failed = total - successful

    # Field coverage
    field_counts = Counter()
    field_confidence_sums = defaultdict(float)

    for extraction in extractions:
        if "dwc" in extraction:
            for field, value in extraction["dwc"].items():
                if value:  # Non-empty
                    field_counts[field] += 1

                    if "dwc_confidence" in extraction:
                        field_confidence_sums[field] += extraction["dwc_confidence"].get(field, 0.0)

    # Average confidences
    avg_confidences = {}
    for field, count in field_counts.items():
        if count > 0:
            avg_confidences[field] = field_confidence_sums[field] / count

    return {
        "total_specimens": total,
        "successful_extractions": successful,
        "failed_extractions": failed,
        "success_rate": successful / total if total > 0 else 0,
        "field_coverage": dict(field_counts),
        "field_coverage_percentage": {
            field: (count / successful * 100) if successful > 0 else 0
            for field, count in field_counts.items()
        },
        "average_confidence": avg_confidences,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Process OpenAI Batch API results"
    )

    # Either batch output file or batch ID
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--input",
        type=Path,
        help="Batch output JSONL file"
    )
    input_group.add_argument(
        "--batch-id",
        type=str,
        help="Batch job ID (will download results)"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory (default: same as input file)"
    )

    args = parser.parse_args()

    # Get input file
    if args.batch_id:
        output_dir = args.output_dir or Path("full_dataset_processing/gpt4omini_batch")
        output_dir.mkdir(parents=True, exist_ok=True)
        input_file = download_batch_results(args.batch_id, output_dir)
    else:
        input_file = args.input
        output_dir = args.output_dir or input_file.parent

    # Validate input
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    print("=" * 70)
    print("PROCESSING BATCH RESULTS")
    print("=" * 70)
    print(f"\n📂 Input: {input_file}")
    print(f"📂 Output: {output_dir}")

    # Process results
    print(f"\n🔄 Processing batch responses...")

    extractions = []
    errors = []

    with open(input_file, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                response = json.loads(line)
                extraction = parse_batch_response(response)

                if extraction:
                    extractions.append(extraction)

                    if "error" in extraction:
                        errors.append(extraction)

                if i % 100 == 0:
                    print(f"  Processed {i} responses...")

            except Exception as e:
                print(f"  ⚠️  Error on line {i}: {e}")
                continue

    print(f"\n✅ Processed {len(extractions)} responses")

    # Write extractions
    output_path = output_dir / "raw.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for extraction in extractions:
            f.write(json.dumps(extraction) + "\n")

    print(f"\n💾 Saved extractions:")
    print(f"   {output_path}")
    print(f"   {len(extractions):,} records")

    # Write errors if any
    if errors:
        error_path = output_dir / "extraction_errors.jsonl"
        with open(error_path, "w", encoding="utf-8") as f:
            for error in errors:
                f.write(json.dumps(error) + "\n")

        print(f"\n⚠️  Saved errors:")
        print(f"   {error_path}")
        print(f"   {len(errors):,} failed extractions")

    # Generate statistics
    stats = generate_statistics(extractions)

    stats_path = output_dir / "extraction_statistics.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print(f"\n📊 Statistics:")
    print(f"   Total specimens:    {stats['total_specimens']:,}")
    print(f"   Successful:         {stats['successful_extractions']:,} ({stats['success_rate']:.1%})")
    print(f"   Failed:             {stats['failed_extractions']:,}")

    # Field coverage summary
    print(f"\n📋 Top 10 Fields by Coverage:")
    sorted_fields = sorted(
        stats["field_coverage_percentage"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    for field, pct in sorted_fields:
        count = stats["field_coverage"][field]
        avg_conf = stats["average_confidence"].get(field, 0.0)
        print(f"   {field:<25} {pct:>6.1f}% ({count:>4} specimens, avg conf: {avg_conf:.2f})")

    print(f"\n💾 Saved statistics: {stats_path}")

    print("\n" + "=" * 70)
    print("✅ BATCH PROCESSING COMPLETE")
    print("=" * 70)
    print(f"\n📍 Next steps:")
    print(f"   1. Validate results:")
    print(f"      python scripts/validate_extraction.py \\")
    print(f"        deliverables/validation/human_validation.jsonl \\")
    print(f"        {output_path}")
    print(f"\n   2. Export to Darwin Core Archive:")
    print(f"      python export_darwin_core.py {output_path}")


if __name__ == "__main__":
    main()
