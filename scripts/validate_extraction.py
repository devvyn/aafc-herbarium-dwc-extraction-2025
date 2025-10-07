#!/usr/bin/env python
"""
Extraction Quality Validation Script

Compares extracted Darwin Core data against human-validated ground truth.
Calculates quality metrics including exact match rate, partial match rate,
and field coverage.

Usage:
    python scripts/validate_extraction.py <ground_truth.jsonl> <extraction.jsonl>

Output:
    - Quality metrics report (JSON)
    - Field-by-field comparison stats
    - Per-specimen validation results
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class ValidationMetrics:
    """Quality metrics for extraction validation."""

    total_specimens: int
    fields_compared: List[str]
    exact_matches: Dict[str, int]
    partial_matches: Dict[str, int]
    field_coverage: Dict[str, int]
    overall_exact_rate: float
    overall_partial_rate: float
    overall_coverage_rate: float


def normalize_text(text: Optional[str]) -> str:
    """Normalize text for comparison (lowercase, strip whitespace)."""
    if not text:
        return ""
    return str(text).lower().strip()


def is_exact_match(extracted: str, ground_truth: str) -> bool:
    """Check if extracted value exactly matches ground truth."""
    return normalize_text(extracted) == normalize_text(ground_truth)


def is_partial_match(extracted: str, ground_truth: str) -> bool:
    """Check if extracted value partially matches ground truth."""
    if not extracted or not ground_truth:
        return False

    extracted_norm = normalize_text(extracted)
    truth_norm = normalize_text(ground_truth)

    # Exact match is also partial match
    if extracted_norm == truth_norm:
        return True

    # Check if one contains the other (substring match)
    if extracted_norm in truth_norm or truth_norm in extracted_norm:
        return True

    # Check for word-level overlap
    extracted_words = set(extracted_norm.split())
    truth_words = set(truth_norm.split())

    if not extracted_words or not truth_words:
        return False

    # At least 50% word overlap = partial match
    overlap = len(extracted_words & truth_words)
    min_words = min(len(extracted_words), len(truth_words))

    return overlap / min_words >= 0.5


def load_jsonl(file_path: Path) -> List[Dict]:
    """Load JSONL file into list of dictionaries."""
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def validate_specimen(
    ground_truth: Dict, extraction: Dict, fields: List[str]
) -> Dict[str, Dict]:
    """Validate a single specimen against ground truth.

    Args:
        ground_truth: Ground truth record with 'corrected' field
        extraction: Extraction record with DWC fields (may be nested under 'dwc' key)
        fields: List of Darwin Core fields to validate

    Returns:
        Dict mapping field names to validation results
    """
    results = {}

    # Ground truth is in the 'corrected' field
    truth_data = ground_truth.get("corrected", {})

    # Extraction data may be nested under 'dwc' key
    extraction_data = extraction.get("dwc", extraction)

    for field in fields:
        extracted_value = extraction_data.get(field, "")
        truth_value = truth_data.get(field, "")

        exact = is_exact_match(extracted_value, truth_value)
        partial = is_partial_match(extracted_value, truth_value)
        has_value = bool(extracted_value)

        results[field] = {
            "extracted": extracted_value,
            "truth": truth_value,
            "exact_match": exact,
            "partial_match": partial,
            "has_value": has_value,
        }

    return results


def calculate_metrics(
    validation_results: List[Dict], fields: List[str]
) -> ValidationMetrics:
    """Calculate aggregate quality metrics from validation results.

    Args:
        validation_results: List of per-specimen validation results
        fields: List of Darwin Core fields validated

    Returns:
        ValidationMetrics with aggregate statistics
    """
    exact_matches = {field: 0 for field in fields}
    partial_matches = {field: 0 for field in fields}
    field_coverage = {field: 0 for field in fields}

    total_specimens = len(validation_results)

    for result in validation_results:
        for field in fields:
            field_result = result.get(field, {})

            if field_result.get("exact_match"):
                exact_matches[field] += 1

            if field_result.get("partial_match"):
                partial_matches[field] += 1

            if field_result.get("has_value"):
                field_coverage[field] += 1

    # Calculate overall rates
    total_comparisons = total_specimens * len(fields)

    overall_exact = sum(exact_matches.values())
    overall_partial = sum(partial_matches.values())
    overall_coverage = sum(field_coverage.values())

    overall_exact_rate = overall_exact / total_comparisons if total_comparisons > 0 else 0
    overall_partial_rate = (
        overall_partial / total_comparisons if total_comparisons > 0 else 0
    )
    overall_coverage_rate = (
        overall_coverage / total_comparisons if total_comparisons > 0 else 0
    )

    return ValidationMetrics(
        total_specimens=total_specimens,
        fields_compared=fields,
        exact_matches=exact_matches,
        partial_matches=partial_matches,
        field_coverage=field_coverage,
        overall_exact_rate=overall_exact_rate,
        overall_partial_rate=overall_partial_rate,
        overall_coverage_rate=overall_coverage_rate,
    )


def format_metrics_report(metrics: ValidationMetrics) -> str:
    """Format validation metrics as human-readable report."""
    lines = [
        "=" * 70,
        "EXTRACTION QUALITY VALIDATION REPORT",
        "=" * 70,
        f"\nTotal Specimens Validated: {metrics.total_specimens}",
        f"Fields Compared: {', '.join(metrics.fields_compared)}",
        "\n" + "=" * 70,
        "OVERALL METRICS",
        "=" * 70,
        f"Exact Match Rate:   {metrics.overall_exact_rate:>6.1%}",
        f"Partial Match Rate: {metrics.overall_partial_rate:>6.1%}",
        f"Field Coverage:     {metrics.overall_coverage_rate:>6.1%}",
        "\n" + "=" * 70,
        "FIELD-BY-FIELD BREAKDOWN",
        "=" * 70,
        f"\n{'Field':<20} {'Exact':<12} {'Partial':<12} {'Coverage':<12}",
        "-" * 70,
    ]

    for field in metrics.fields_compared:
        exact_count = metrics.exact_matches[field]
        partial_count = metrics.partial_matches[field]
        coverage_count = metrics.field_coverage[field]

        exact_pct = exact_count / metrics.total_specimens if metrics.total_specimens > 0 else 0
        partial_pct = (
            partial_count / metrics.total_specimens if metrics.total_specimens > 0 else 0
        )
        coverage_pct = (
            coverage_count / metrics.total_specimens if metrics.total_specimens > 0 else 0
        )

        lines.append(
            f"{field:<20} {exact_pct:>6.1%} ({exact_count:>3}) "
            f"{partial_pct:>6.1%} ({partial_count:>3}) "
            f"{coverage_pct:>6.1%} ({coverage_count:>3})"
        )

    lines.extend(["=" * 70, ""])

    return "\n".join(lines)


def main():
    """Main validation workflow."""
    if len(sys.argv) < 3:
        print(
            "Usage: python scripts/validate_extraction.py <ground_truth.jsonl> <extraction.jsonl>"
        )
        print("\nExample:")
        print(
            "  python scripts/validate_extraction.py deliverables/validation/human_validation.jsonl deliverables/v1.0_vision_api_baseline.jsonl"
        )
        sys.exit(1)

    ground_truth_path = Path(sys.argv[1])
    extraction_path = Path(sys.argv[2])

    # Validate inputs
    if not ground_truth_path.exists():
        print(f"Error: Ground truth file not found: {ground_truth_path}")
        sys.exit(1)

    if not extraction_path.exists():
        print(f"Error: Extraction file not found: {extraction_path}")
        sys.exit(1)

    # Load data
    print(f"Loading ground truth from: {ground_truth_path}")
    ground_truth_records = load_jsonl(ground_truth_path)

    print(f"Loading extraction results from: {extraction_path}")
    extraction_records = load_jsonl(extraction_path)

    # Create lookup by sha256
    extraction_by_sha = {rec["sha256"]: rec for rec in extraction_records}

    # Darwin Core fields to validate
    dwc_fields = [
        "catalogNumber",
        "scientificName",
        "eventDate",
        "recordedBy",
        "locality",
        "stateProvince",
        "country",
    ]

    # Validate each specimen
    validation_results = []

    print(f"\nValidating {len(ground_truth_records)} specimens...")

    for gt_record in ground_truth_records:
        sha256 = gt_record["sha256"]

        if sha256 not in extraction_by_sha:
            print(f"Warning: No extraction found for specimen {sha256}")
            continue

        extraction = extraction_by_sha[sha256]

        result = validate_specimen(gt_record, extraction, dwc_fields)
        validation_results.append(result)

    # Calculate metrics
    metrics = calculate_metrics(validation_results, dwc_fields)

    # Print report
    print("\n" + format_metrics_report(metrics))

    # Output JSON metrics
    metrics_json = {
        "total_specimens": metrics.total_specimens,
        "fields_compared": metrics.fields_compared,
        "exact_matches": metrics.exact_matches,
        "partial_matches": metrics.partial_matches,
        "field_coverage": metrics.field_coverage,
        "overall_exact_rate": round(metrics.overall_exact_rate, 4),
        "overall_partial_rate": round(metrics.overall_partial_rate, 4),
        "overall_coverage_rate": round(metrics.overall_coverage_rate, 4),
    }

    output_path = Path("validation_metrics.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics_json, f, indent=2)

    print(f"✅ Metrics saved to: {output_path}")

    # Exit with appropriate code
    if metrics.overall_exact_rate < 0.5:
        print(
            f"\n⚠️  WARNING: Exact match rate ({metrics.overall_exact_rate:.1%}) below 50% threshold"
        )
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
