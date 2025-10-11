#!/usr/bin/env python3
"""
Analyze Empty/Failed Extraction Records

Investigates specimens that failed extraction or returned empty data.
Identifies patterns, API errors, and provides recommendations.

Usage:
    python scripts/analyze_empty_records.py \\
        --input full_dataset_processing/openrouter_run_20251010_115131/raw.jsonl \\
        --output analysis_report.json
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def analyze_empty_records(results_file: Path) -> Dict:
    """
    Analyze empty/failed extraction records.

    Args:
        results_file: Path to raw.jsonl

    Returns:
        Analysis results dictionary
    """
    print(f"📂 Loading results from {results_file}...")

    empty_records = []
    api_errors = []
    successful_records = []

    with open(results_file) as f:
        for line_num, line in enumerate(f, 1):
            try:
                record = json.loads(line)

                # Check if extraction failed
                if "error" in record:
                    api_errors.append(
                        {
                            "line": line_num,
                            "image": record.get("image", "unknown"),
                            "error": record["error"],
                            "timestamp": record.get("timestamp"),
                            "model": record.get("model"),
                        }
                    )

                # Check if DWC data is empty
                elif not record.get("dwc") or not any(record.get("dwc", {}).values()):
                    empty_records.append(
                        {
                            "line": line_num,
                            "image": record.get("image", "unknown"),
                            "timestamp": record.get("timestamp"),
                            "model": record.get("model"),
                            "dwc": record.get("dwc", {}),
                        }
                    )

                else:
                    successful_records.append(record)

            except json.JSONDecodeError as e:
                print(f"⚠️  Line {line_num}: JSON decode error - {e}")

    print("\n✅ Loaded:")
    print(f"   - Successful: {len(successful_records)}")
    print(f"   - API errors: {len(api_errors)}")
    print(f"   - Empty data: {len(empty_records)}")

    # Analyze API errors
    print("\n🔍 Analyzing API errors...")
    error_patterns = analyze_api_errors(api_errors)

    # Analyze empty records
    print("🔍 Analyzing empty records...")
    empty_patterns = analyze_empty_patterns(empty_records)

    # Temporal analysis
    print("🔍 Analyzing temporal patterns...")
    temporal = analyze_temporal_patterns(api_errors, empty_records)

    return {
        "summary": {
            "total_records": len(successful_records) + len(api_errors) + len(empty_records),
            "successful": len(successful_records),
            "api_errors": len(api_errors),
            "empty_data": len(empty_records),
            "failure_rate": (len(api_errors) + len(empty_records))
            / (len(successful_records) + len(api_errors) + len(empty_records))
            * 100,
        },
        "api_errors": error_patterns,
        "empty_records": empty_patterns,
        "temporal_analysis": temporal,
        "recommendations": generate_recommendations(error_patterns, empty_patterns, temporal),
    }


def analyze_api_errors(errors: List[Dict]) -> Dict:
    """Analyze patterns in API errors."""
    if not errors:
        return {"count": 0, "patterns": {}}

    # Group by error type
    error_types = Counter(err["error"] for err in errors)

    # Group by error message patterns
    patterns = defaultdict(list)
    for err in errors:
        error_msg = err["error"]

        # Categorize errors
        if "timeout" in error_msg.lower():
            patterns["timeout"].append(err)
        elif "520" in error_msg or "502" in error_msg or "503" in error_msg:
            patterns["server_error"].append(err)
        elif "rate" in error_msg.lower() or "429" in error_msg:
            patterns["rate_limit"].append(err)
        elif "ended prematurely" in error_msg.lower():
            patterns["connection_dropped"].append(err)
        elif "no such file" in error_msg.lower() or "not found" in error_msg.lower():
            patterns["file_missing"].append(err)
        else:
            patterns["other"].append(err)

    return {
        "count": len(errors),
        "error_types": dict(error_types.most_common()),
        "categorized": {
            category: {
                "count": len(errs),
                "examples": [e["error"] for e in errs[:3]],
                "first_occurrence": errs[0]["line"] if errs else None,
                "last_occurrence": errs[-1]["line"] if errs else None,
            }
            for category, errs in patterns.items()
        },
    }


def analyze_empty_patterns(empty: List[Dict]) -> Dict:
    """Analyze patterns in empty extractions."""
    if not empty:
        return {"count": 0, "patterns": {}}

    # Check if DWC is completely empty or has empty values
    completely_empty = [r for r in empty if not r.get("dwc")]
    has_structure = [r for r in empty if r.get("dwc")]

    return {
        "count": len(empty),
        "completely_empty": len(completely_empty),
        "empty_fields": len(has_structure),
        "examples": [
            {
                "image": r["image"][:50],
                "dwc_structure": bool(r.get("dwc")),
                "field_count": len(r.get("dwc", {})),
            }
            for r in empty[:5]
        ],
    }


def analyze_temporal_patterns(errors: List[Dict], empty: List[Dict]) -> Dict:
    """Analyze temporal patterns in failures."""
    all_failures = errors + empty

    if not all_failures:
        return {"pattern": "No failures"}

    # Sort by line number (proxy for time)
    all_failures.sort(key=lambda x: x["line"])

    # Find clusters
    first_failure = all_failures[0]["line"]
    last_failure = all_failures[-1]["line"]

    # Group into time windows (every 100 records)
    window_size = 100
    windows = defaultdict(int)

    for failure in all_failures:
        window = (failure["line"] // window_size) * window_size
        windows[window] += 1

    # Find burst windows (>10 failures in 100 records)
    burst_windows = {w: count for w, count in windows.items() if count > 10}

    return {
        "first_failure_at": first_failure,
        "last_failure_at": last_failure,
        "failure_span": last_failure - first_failure,
        "burst_windows": burst_windows if burst_windows else None,
        "pattern": "clustered" if burst_windows else "distributed",
    }


def generate_recommendations(
    error_patterns: Dict, empty_patterns: Dict, temporal: Dict
) -> List[str]:
    """Generate actionable recommendations."""
    recommendations = []

    # API error recommendations
    if error_patterns.get("categorized", {}).get("file_missing"):
        recommendations.append(
            "CRITICAL: Implement JIT caching with graceful fallback (see io_utils/jit_cache.py)"
        )
        recommendations.append("Use prepare_images_cached.py to pre-download images")

    if error_patterns.get("categorized", {}).get("server_error"):
        recommendations.append(
            "API instability detected: Implement retry logic with exponential backoff"
        )
        recommendations.append("Consider switching to batch API if available")

    if error_patterns.get("categorized", {}).get("rate_limit"):
        recommendations.append("Rate limiting detected: Add throttling between requests")
        recommendations.append("Consider API key rotation or batch processing")

    if error_patterns.get("categorized", {}).get("connection_dropped"):
        recommendations.append("Connection stability issues: Implement checkpointing")
        recommendations.append("Add resume capability from last successful specimen")

    # Empty record recommendations
    if empty_patterns.get("count", 0) > 0:
        recommendations.append(
            f"Investigate {empty_patterns['count']} empty extractions - may indicate prompt issues"
        )
        recommendations.append("Review prompt engineering for edge cases")
        recommendations.append("Consider fallback extraction strategies for low-quality images")

    # Temporal pattern recommendations
    if temporal.get("burst_windows"):
        recommendations.append("Clustered failures detected - likely external service issue")
        recommendations.append("Implement monitoring and alerting for burst failures")

    if not recommendations:
        recommendations.append("No critical issues detected - extraction generally successful")

    return recommendations


def main():
    parser = argparse.ArgumentParser(description="Analyze empty/failed extraction records")
    parser.add_argument("--input", type=Path, required=True, help="Input raw.jsonl file")
    parser.add_argument("--output", type=Path, help="Output JSON report (default: print to stdout)")

    args = parser.parse_args()

    print("=" * 70)
    print("EMPTY RECORDS ANALYSIS")
    print("=" * 70)
    print()

    # Run analysis
    results = analyze_empty_records(args.input)

    # Generate report
    print("\n" + "=" * 70)
    print("ANALYSIS RESULTS")
    print("=" * 70)

    print("\n📊 Summary:")
    print(f"   Total records: {results['summary']['total_records']}")
    print(
        f"   Successful: {results['summary']['successful']} ({100 - results['summary']['failure_rate']:.1f}%)"
    )
    print(
        f"   Failed: {results['summary']['api_errors'] + results['summary']['empty_data']} ({results['summary']['failure_rate']:.1f}%)"
    )
    print(f"     - API errors: {results['summary']['api_errors']}")
    print(f"     - Empty data: {results['summary']['empty_data']}")

    if results["api_errors"]["categorized"]:
        print("\n🔴 API Error Breakdown:")
        for category, data in results["api_errors"]["categorized"].items():
            if data["count"] > 0:
                print(f"   {category}: {data['count']} occurrences")
                if data["examples"]:
                    print(f"      Example: {data['examples'][0][:80]}")

    if results["temporal_analysis"]["pattern"] == "clustered":
        print("\n⏰ Temporal Pattern: CLUSTERED failures detected")
        print(f"   First failure: line {results['temporal_analysis']['first_failure_at']}")
        print(f"   Last failure: line {results['temporal_analysis']['last_failure_at']}")
        if results["temporal_analysis"]["burst_windows"]:
            print(f"   Burst windows: {len(results['temporal_analysis']['burst_windows'])}")

    print("\n💡 Recommendations:")
    for i, rec in enumerate(results["recommendations"], 1):
        print(f"   {i}. {rec}")

    # Save to file if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Full report saved: {args.output}")

    print()


if __name__ == "__main__":
    main()
