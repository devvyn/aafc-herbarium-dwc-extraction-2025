#!/usr/bin/env python
"""
Compare Extraction Strategies

Compares multiple extraction strategies against ground truth.
Ranks strategies by accuracy, field coverage, and confidence.

Usage:
    # After all experimental batches complete:
    python scripts/compare_strategies.py \
        --ground-truth deliverables/validation/human_validation.jsonl \
        --experiments experiments.json \
        --output comparison_results.json
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
except ImportError:
    print("Error: rich library not installed")
    print("Install with: uv add rich")
    sys.exit(1)


console = Console()


def load_extractions(jsonl_file: Path) -> List[Dict]:
    """Load extraction results from JSONL."""
    if not jsonl_file.exists():
        return []

    with open(jsonl_file, "r") as f:
        return [json.loads(line) for line in f]


def normalize_value(value: str) -> str:
    """Normalize field value for comparison."""
    if not value:
        return ""

    # Lowercase, strip whitespace
    normalized = str(value).lower().strip()

    # Remove extra whitespace
    normalized = " ".join(normalized.split())

    return normalized


def compare_field(extracted: str, truth: str) -> Dict[str, any]:
    """Compare a single field value against ground truth.

    Returns:
        Dict with exact_match, partial_match, and similarity score
    """
    ext_norm = normalize_value(extracted)
    truth_norm = normalize_value(truth)

    if not truth_norm:
        return {"exact_match": False, "partial_match": False, "similarity": 0.0}

    if not ext_norm:
        return {"exact_match": False, "partial_match": False, "similarity": 0.0}

    # Exact match
    if ext_norm == truth_norm:
        return {"exact_match": True, "partial_match": True, "similarity": 1.0}

    # Partial match (one contains the other)
    if ext_norm in truth_norm or truth_norm in ext_norm:
        similarity = min(len(ext_norm), len(truth_norm)) / max(len(ext_norm), len(truth_norm))
        return {"exact_match": False, "partial_match": True, "similarity": similarity}

    # No match
    return {"exact_match": False, "partial_match": False, "similarity": 0.0}


def validate_extraction(extracted: Dict, ground_truth: Dict) -> Dict:
    """Validate a single extraction against ground truth.

    Returns:
        Dict with per-field comparison results
    """
    ext_dwc = extracted.get("dwc", {})
    truth_dwc = ground_truth.get("dwc", {})

    results = {}

    # Compare all fields in ground truth
    for field, truth_value in truth_dwc.items():
        ext_value = ext_dwc.get(field, "")
        results[field] = compare_field(ext_value, truth_value)

    return results


def calculate_strategy_metrics(extractions: List[Dict], ground_truth: List[Dict]) -> Dict:
    """Calculate comprehensive metrics for a strategy.

    Returns:
        Dict with accuracy, coverage, confidence metrics
    """
    # Build lookup by SHA256
    truth_lookup = {gt["sha256"]: gt for gt in ground_truth}

    # Per-field aggregates
    field_stats = defaultdict(
        lambda: {
            "exact_matches": 0,
            "partial_matches": 0,
            "total_comparisons": 0,
            "confidence_sum": 0.0,
            "present_in_extracted": 0,
            "present_in_truth": 0,
        }
    )

    total_specimens = 0

    for extraction in extractions:
        sha256 = extraction.get("sha256")
        if sha256 not in truth_lookup:
            continue

        total_specimens += 1
        truth = truth_lookup[sha256]

        # Validate
        field_results = validate_extraction(extraction, truth)

        # Aggregate stats
        ext_dwc = extraction.get("dwc", {})
        truth_dwc = truth.get("dwc", {})
        confidences = extraction.get("dwc_confidence", {})

        for field, result in field_results.items():
            stats = field_stats[field]

            # Comparison counts
            stats["total_comparisons"] += 1

            if result["exact_match"]:
                stats["exact_matches"] += 1
                stats["partial_matches"] += 1
            elif result["partial_match"]:
                stats["partial_matches"] += 1

            # Presence counts
            if ext_dwc.get(field):
                stats["present_in_extracted"] += 1

            if truth_dwc.get(field):
                stats["present_in_truth"] += 1

            # Confidence
            conf = confidences.get(field, 0.0)
            if conf:
                stats["confidence_sum"] += conf

    # Calculate final metrics
    metrics = {"total_specimens": total_specimens, "fields": {}}

    for field, stats in field_stats.items():
        total = stats["total_comparisons"]
        if total == 0:
            continue

        metrics["fields"][field] = {
            "exact_accuracy": stats["exact_matches"] / total,
            "partial_accuracy": stats["partial_matches"] / total,
            "precision": stats["exact_matches"] / stats["present_in_extracted"]
            if stats["present_in_extracted"] > 0
            else 0,
            "recall": stats["exact_matches"] / stats["present_in_truth"]
            if stats["present_in_truth"] > 0
            else 0,
            "coverage": stats["present_in_extracted"] / total,
            "avg_confidence": stats["confidence_sum"] / stats["present_in_extracted"]
            if stats["present_in_extracted"] > 0
            else 0,
            "exact_matches": stats["exact_matches"],
            "partial_matches": stats["partial_matches"],
            "total": total,
        }

    # Overall metrics
    all_exact = sum(f["exact_matches"] for f in metrics["fields"].values())
    all_partial = sum(f["partial_matches"] for f in metrics["fields"].values())
    all_total = sum(f["total"] for f in metrics["fields"].values())

    metrics["overall"] = {
        "exact_accuracy": all_exact / all_total if all_total > 0 else 0,
        "partial_accuracy": all_partial / all_total if all_total > 0 else 0,
        "avg_confidence": sum(f["avg_confidence"] * f["total"] for f in metrics["fields"].values())
        / all_total
        if all_total > 0
        else 0,
    }

    return metrics


def load_experiment_results(experiments_file: Path) -> List[Dict]:
    """Load experiment metadata and results."""
    if not experiments_file.exists():
        console.print(f"[red]Error: Experiments file not found: {experiments_file}[/red]")
        return []

    with open(experiments_file, "r") as f:
        data = json.loads(f.read())

    experiments = data.get("experiments", [])

    # Load raw.jsonl for each experiment
    for exp in experiments:
        output_dir = Path(exp["output_dir"])
        raw_file = output_dir / "raw.jsonl"

        if raw_file.exists():
            exp["extractions"] = load_extractions(raw_file)
        else:
            exp["extractions"] = []

    return experiments


def display_comparison(experiments: List[Dict], ground_truth: List[Dict]):
    """Display comparison table."""
    console.print(Panel("[bold cyan]Strategy Comparison[/bold cyan]", expand=False))

    # Calculate metrics for each strategy
    strategy_metrics = []

    for exp in experiments:
        if not exp["extractions"]:
            console.print(f"[yellow]⏳ {exp['name']}: No results yet[/yellow]")
            continue

        metrics = calculate_strategy_metrics(exp["extractions"], ground_truth)
        strategy_metrics.append(
            {"name": exp["name"], "description": exp["description"], "metrics": metrics}
        )

    if not strategy_metrics:
        console.print("[yellow]No completed strategies to compare[/yellow]")
        return strategy_metrics

    # Overall comparison table
    table = Table(title="Overall Strategy Performance")
    table.add_column("Strategy", style="cyan")
    table.add_column("Specimens", justify="right")
    table.add_column("Exact Acc", justify="right", style="green")
    table.add_column("Partial Acc", justify="right", style="yellow")
    table.add_column("Avg Conf", justify="right", style="blue")

    for strategy in sorted(
        strategy_metrics, key=lambda s: s["metrics"]["overall"]["exact_accuracy"], reverse=True
    ):
        name = strategy["name"]
        m = strategy["metrics"]

        table.add_row(
            name,
            str(m["total_specimens"]),
            f"{m['overall']['exact_accuracy']:.1%}",
            f"{m['overall']['partial_accuracy']:.1%}",
            f"{m['overall']['avg_confidence']:.2f}",
        )

    console.print("\n", table)

    # Per-field comparison for top fields
    console.print("\n[bold]Key Field Performance[/bold]")

    key_fields = ["scientificName", "catalogNumber", "recordedBy", "locality", "eventDate"]

    for field in key_fields:
        field_table = Table(title=f"{field}", show_header=True)
        field_table.add_column("Strategy", style="cyan")
        field_table.add_column("Exact", justify="right", style="green")
        field_table.add_column("Partial", justify="right", style="yellow")
        field_table.add_column("Coverage", justify="right")
        field_table.add_column("Conf", justify="right", style="blue")

        for strategy in strategy_metrics:
            name = strategy["name"]
            fields = strategy["metrics"]["fields"]

            if field not in fields:
                continue

            f = fields[field]
            field_table.add_row(
                name,
                f"{f['exact_accuracy']:.1%}",
                f"{f['partial_accuracy']:.1%}",
                f"{f['coverage']:.1%}",
                f"{f['avg_confidence']:.2f}",
            )

        console.print("\n", field_table)

    return strategy_metrics


def main():
    parser = argparse.ArgumentParser(description="Compare extraction strategies")
    parser.add_argument("--ground-truth", type=Path, required=True, help="Ground truth JSONL file")
    parser.add_argument(
        "--experiments",
        type=Path,
        default=Path("experiments.json"),
        help="Experiments metadata JSON",
    )
    parser.add_argument("--output", type=Path, help="Output comparison results JSON")

    args = parser.parse_args()

    # Load ground truth
    ground_truth = load_extractions(args.ground_truth)
    if not ground_truth:
        console.print(f"[red]Error: No ground truth data found in {args.ground_truth}[/red]")
        sys.exit(1)

    console.print(f"[green]✅ Loaded {len(ground_truth)} ground truth specimens[/green]")

    # Load experiments
    experiments = load_experiment_results(args.experiments)
    if not experiments:
        console.print("[red]Error: No experiments found[/red]")
        sys.exit(1)

    console.print(f"[green]✅ Loaded {len(experiments)} experiments[/green]")

    # Display comparison
    strategy_metrics = display_comparison(experiments, ground_truth)

    # Save results
    if args.output and strategy_metrics:
        with open(args.output, "w") as f:
            json.dump(strategy_metrics, f, indent=2)

        console.print(f"\n[green]💾 Saved comparison results: {args.output}[/green]")

    # Recommend winner
    if strategy_metrics:
        winner = max(strategy_metrics, key=lambda s: s["metrics"]["overall"]["exact_accuracy"])
        console.print(f"\n[bold green]🏆 Recommended strategy: {winner['name']}[/bold green]")
        console.print(f"   {winner['description']}")
        console.print(f"   Exact accuracy: {winner['metrics']['overall']['exact_accuracy']:.1%}")


if __name__ == "__main__":
    main()
