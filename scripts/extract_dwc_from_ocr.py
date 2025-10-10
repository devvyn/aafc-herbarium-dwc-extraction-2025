#!/usr/bin/env python3
"""Extract Darwin Core fields from OCR text in raw.jsonl files.

This script bypasses the database pipeline and directly processes OCR text
to extract Darwin Core fields. It can use either:
1. Simple rule-based extraction (no API calls, free)
2. GPT-based extraction (requires OPENAI_API_KEY, costs money)

Usage:
    python scripts/extract_dwc_from_ocr.py <run_directory> [--method simple|gpt]
    python scripts/extract_dwc_from_ocr.py full_dataset_processing/run_20250930_145826

Output:
    - occurrence.csv: Darwin Core occurrence data
    - extraction_report.json: Quality metrics and statistics
"""

import json
import csv
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import Counter


def simple_extract_dwc(ocr_text: str) -> Dict[str, str]:
    """Extract Darwin Core fields using simple regex patterns.

    This is a rule-based extractor that looks for common patterns in
    herbarium specimen labels from AAFC Regina Research Station.
    """
    dwc = {}
    text = ocr_text

    # Scientific name (usually early in label, often with botanical formatting)
    # Look for Latin binomial pattern
    sci_name_match = re.search(
        r"\b([A-Z][a-z]+\s+[a-z]+(?:\s+(?:var\.|subsp\.|f\.)\s+[a-z]+)?)", text
    )
    if sci_name_match:
        dwc["scientificName"] = sci_name_match.group(1).strip()

    # Collector name
    # Look for "Collector" label followed by name
    collector_match = re.search(
        r"(?:Collector[:\.]?|Coll\.)\s*([A-Z][A-Za-z\.\s]+?)(?:\s*Date|$)", text, re.IGNORECASE
    )
    if collector_match:
        dwc["recordedBy"] = collector_match.group(1).strip()

    # Collection date
    # Look for dates in various formats
    date_patterns = [
        r"(?:Date[:\.]?)\s*([A-Z][a-z]+\.?\s+\d{1,2},?\s+\d{4})",  # Aug. 22, 1985
        r"(?:Date[:\.]?)\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",  # 22-08-1985
        r"(\d{4})",  # Just year
    ]
    for pattern in date_patterns:
        date_match = re.search(pattern, text, re.IGNORECASE)
        if date_match:
            dwc["eventDate"] = date_match.group(1).strip()
            break

    # Locality
    # Look for location-related keywords
    locality_match = re.search(
        r"(?:Locality|Location|Habitat)[:\.]?\s*([A-Za-z0-9\s,\-]+?)(?:\s*(?:Collector|Date|Host)|$)",
        text,
        re.IGNORECASE,
    )
    if locality_match:
        dwc["locality"] = locality_match.group(1).strip()

    # Country (default to Canada for AAFC specimens)
    if "CANADA" in text.upper() or "REGINA" in text.upper() or "SASKATCHEWAN" in text.upper():
        dwc["country"] = "Canada"
        dwc["stateProvince"] = "Saskatchewan"

    # Institution code (if AAFC/Agriculture Canada mentioned)
    if "AGRICULTURE CANADA" in text.upper() or "AAFC" in text.upper():
        dwc["institutionCode"] = "AAFC"
        dwc["collectionCode"] = "REGINA"

    # Catalog number (look for specimen numbers)
    catalog_match = re.search(r"(?:No\.|Number|#)\s*([A-Z]?[-]?\d+)", text, re.IGNORECASE)
    if catalog_match:
        dwc["catalogNumber"] = catalog_match.group(1).strip()

    # Basis of record (always PreservedSpecimen for herbarium)
    dwc["basisOfRecord"] = "PreservedSpecimen"

    return dwc


def gpt_extract_dwc(
    ocr_text: str, model: str = "gpt-4o-mini"
) -> Tuple[Dict[str, str], Dict[str, float]]:
    """Extract Darwin Core fields using GPT API.

    Requires OPENAI_API_KEY environment variable.
    """
    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: OpenAI SDK not available. Install with: uv add openai", file=sys.stderr)
        return {}, {}

    client = OpenAI()  # Will raise if OPENAI_API_KEY not set

    prompt = """Extract Darwin Core fields from this herbarium specimen label text.
Return JSON with Darwin Core field names as keys and objects with 'value' and 'confidence' (0.0-1.0).

Required fields if present: scientificName, recordedBy, eventDate, locality, country, stateProvince,
institutionCode, catalogNumber, collectionCode, habitat, identifiedBy, basisOfRecord.

Label text:
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a botanical data extraction expert. Extract Darwin Core fields from specimen labels.",
                },
                {"role": "user", "content": prompt + ocr_text},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        data = json.loads(response.choices[0].message.content)
        dwc = {
            k: v.get("value", "") for k, v in data.items() if isinstance(v, dict) and v.get("value")
        }
        confidences = {
            k: float(v.get("confidence", 0.0)) for k, v in data.items() if isinstance(v, dict)
        }

        return dwc, confidences

    except Exception as exc:
        print(f"ERROR: GPT extraction failed: {exc}", file=sys.stderr)
        return {}, {}


def process_run_directory(
    run_dir: Path, method: str = "simple", limit: Optional[int] = None
) -> Tuple[List[Dict[str, str]], Dict[str, any]]:
    """Process all records in a run directory using candidates.db for OCR text."""

    import sqlite3

    candidates_db = run_dir / "candidates.db"
    if not candidates_db.exists():
        raise FileNotFoundError(f"No candidates.db found in {run_dir}")

    print(f"Processing {candidates_db}")
    print(f"Extraction method: {method}")

    records = []
    stats = {
        "total_records": 0,
        "successful_extractions": 0,
        "failed_extractions": 0,
        "empty_ocr_text": 0,
        "field_coverage": Counter(),
        "start_time": datetime.now().isoformat(),
    }

    # Connect to candidates database
    conn = sqlite3.connect(candidates_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all OCR results
    query = "SELECT image, value, engine, confidence, error FROM candidates"
    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)

    for row in cursor:
        try:
            stats["total_records"] += 1

            image_name = row["image"]
            ocr_text = row["value"]
            engine = row["engine"]
            ocr_confidence = row["confidence"]
            has_error = row["error"]

            specimen_id = (
                Path(image_name).stem if image_name else f"record_{stats['total_records']}"
            )

            if not ocr_text or has_error:
                print(
                    f"WARNING: No OCR text for {specimen_id} (error={has_error})", file=sys.stderr
                )
                stats["empty_ocr_text"] += 1
                continue

            # Extract DWC fields
            if method == "simple":
                dwc_fields = simple_extract_dwc(ocr_text)
                confidences = {k: 0.7 for k in dwc_fields}  # Assume moderate confidence
            elif method == "gpt":
                dwc_fields, confidences = gpt_extract_dwc(ocr_text)
            else:
                raise ValueError(f"Unknown extraction method: {method}")

            if dwc_fields:
                # Add metadata
                dwc_fields["specimen_id"] = specimen_id
                dwc_fields["image"] = image_name
                dwc_fields["ocr_engine"] = engine
                dwc_fields["ocr_confidence"] = str(round(ocr_confidence, 3))
                dwc_fields["extraction_method"] = method

                records.append(dwc_fields)
                stats["successful_extractions"] += 1

                # Track field coverage
                for field in dwc_fields:
                    stats["field_coverage"][field] += 1
            else:
                stats["failed_extractions"] += 1

            if stats["total_records"] % 100 == 0:
                print(f"Processed {stats['total_records']} records...", file=sys.stderr)

        except Exception as e:
            print(f"ERROR: Failed to process {image_name}: {e}", file=sys.stderr)
            stats["failed_extractions"] += 1

    conn.close()
    stats["end_time"] = datetime.now().isoformat()

    return records, stats


def write_occurrence_csv(records: List[Dict[str, str]], output_path: Path):
    """Write records to Darwin Core occurrence CSV."""
    if not records:
        print("WARNING: No records to write", file=sys.stderr)
        return

    # Get all unique field names
    all_fields = set()
    for record in records:
        all_fields.update(record.keys())

    # Sort fields for consistent column order
    fieldnames = sorted(all_fields)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"Wrote {len(records)} records to {output_path}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    run_dir = Path(sys.argv[1])
    method = sys.argv[2] if len(sys.argv) > 2 else "simple"

    if not run_dir.exists():
        print(f"ERROR: Directory not found: {run_dir}", file=sys.stderr)
        sys.exit(1)

    if method not in ["simple", "gpt"]:
        print(f"ERROR: Unknown method '{method}'. Use 'simple' or 'gpt'", file=sys.stderr)
        sys.exit(1)

    # Process records
    print(f"\nExtracting Darwin Core fields from {run_dir}")
    records, stats = process_run_directory(run_dir, method=method)

    # Write outputs
    output_dir = run_dir / "extraction_output"
    output_dir.mkdir(exist_ok=True)

    occurrence_csv = output_dir / "occurrence.csv"
    report_json = output_dir / "extraction_report.json"

    write_occurrence_csv(records, occurrence_csv)

    with open(report_json, "w") as f:
        json.dump(stats, f, indent=2, default=str)

    # Print summary
    print(f"\n{'='*60}")
    print("EXTRACTION SUMMARY")
    print(f"{'='*60}")
    print(f"Total records processed: {stats['total_records']}")
    print(f"Successful extractions: {stats['successful_extractions']}")
    print(f"Failed extractions: {stats['failed_extractions']}")
    print(f"Empty OCR text: {stats['empty_ocr_text']}")
    print("\nField coverage (top 10):")
    for field, count in stats["field_coverage"].most_common(10):
        pct = (count / stats["total_records"] * 100) if stats["total_records"] > 0 else 0
        print(f"  {field:30s}: {count:4d} ({pct:5.1f}%)")
    print(f"\nOutputs written to: {output_dir}")
    print(f"  - {occurrence_csv.name}")
    print(f"  - {report_json.name}")


if __name__ == "__main__":
    main()
