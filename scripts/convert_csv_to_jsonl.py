#!/usr/bin/env python3
"""
Convert Vision API CSV extraction to JSONL format for web review.

Transforms flat CSV (v1.0) into structured JSONL (v2.0 format) to enable
web-based review interface.
"""

import csv
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any


def csv_to_jsonl_record(row: Dict[str, str]) -> Dict[str, Any]:
    """
    Convert single CSV row to JSONL record format.

    Args:
        row: CSV row as dictionary

    Returns:
        JSONL record with confidence scores and metadata
    """
    # Use OCR confidence as baseline for all fields
    ocr_confidence = float(row.get("ocr_confidence", 0.8))

    # Build Darwin Core section with confidence scores
    dwc = {}

    # Map CSV fields to DwC terms with confidence
    field_mapping = {
        "basisOfRecord": "basisOfRecord",
        "catalogNumber": "catalogNumber",
        "scientificName": "scientificName",
        "eventDate": "eventDate",
        "recordedBy": "recordedBy",
        "country": "country",
        "stateProvince": "stateProvince",
        "locality": "locality",
        "institutionCode": "institutionCode",
        "collectionCode": "collectionCode",
    }

    for csv_field, dwc_field in field_mapping.items():
        value = row.get(csv_field, "").strip()

        # Adjust confidence based on field presence and quality
        if value:
            # Lower confidence for suspicious values
            confidence = ocr_confidence
            if value in ["Identified by", "Checked by", "Habitab collector"]:
                confidence = 0.3  # Known OCR errors
            elif csv_field == "catalogNumber" and not value.isdigit():
                confidence = 0.5  # Mixed format
        else:
            confidence = 0.0

        dwc[dwc_field] = {"value": value, "confidence": confidence}

    # Build full record
    record = {
        "image": row.get("image", ""),
        "specimen_id": row.get("specimen_id", ""),
        "model": "vision-api",
        "provider": "apple",
        "extraction_method": row.get("extraction_method", "simple"),
        "ocr_engine": row.get("ocr_engine", "vision"),
        "dwc": dwc,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "converted_from_csv": True,
    }

    return record


def convert_csv_to_jsonl(csv_path: Path, jsonl_path: Path) -> int:
    """
    Convert entire CSV file to JSONL format.

    Args:
        csv_path: Input CSV file
        jsonl_path: Output JSONL file

    Returns:
        Number of records converted
    """
    records_converted = 0

    with open(csv_path, "r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)

        with open(jsonl_path, "w", encoding="utf-8") as jsonl_file:
            for row in reader:
                record = csv_to_jsonl_record(row)
                jsonl_file.write(json.dumps(record) + "\n")
                records_converted += 1

    return records_converted


def main():
    """Main conversion workflow."""
    # Paths
    csv_path = Path("deliverables/v1.0_vision_baseline/occurrence.csv")
    jsonl_path = Path("deliverables/v1.0_vision_baseline/raw.jsonl")

    print("=" * 70)
    print("CSV → JSONL CONVERTER FOR WEB REVIEW")
    print("=" * 70)
    print(f"Input:  {csv_path}")
    print(f"Output: {jsonl_path}")
    print()

    if not csv_path.exists():
        print(f"❌ Error: CSV file not found: {csv_path}")
        return 1

    print("🔄 Converting CSV to JSONL format...")
    records = convert_csv_to_jsonl(csv_path, jsonl_path)

    print(f"✅ Converted {records} records")
    print(f"📁 Output: {jsonl_path}")
    print()
    print("🌐 Ready for web review!")
    print(
        "   Run: uv run python cli.py review --extraction-dir deliverables/v1.0_vision_baseline --port 5002"
    )
    print()

    return 0


if __name__ == "__main__":
    exit(main())
