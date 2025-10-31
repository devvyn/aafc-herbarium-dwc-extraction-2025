#!/usr/bin/env python
"""
Experiment Orchestrator - Parallel Batch Testing

Submits multiple experimental batches in parallel and tracks results.
Enables rapid testing of different prompt strategies.

Usage:
    python scripts/experiment_orchestrator.py --submit
    python scripts/experiment_orchestrator.py --status
    python scripts/experiment_orchestrator.py --compare
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

try:
    from openai import OpenAI
except ImportError:
    print("Error: OpenAI SDK not installed")
    print("Install with: uv add openai")
    sys.exit(1)


EXPERIMENTS = [
    {
        "name": "baseline_aafc",
        "description": "Current AAFC-optimized prompts (submitted manually)",
        "task": "image_to_dwc_v2_aafc",
        "output_dir": "full_dataset_processing/gpt4omini_batch_test",
        "batch_id": "batch_68e47d3796d08190b99e9e73fd5aca52",  # Already submitted
        "status": "submitted",
        "cost": 0.03,
    },
    {
        "name": "few_shot",
        "description": "Few-shot learning with 3 example extractions",
        "task": "image_to_dwc_few_shot",
        "output_dir": "full_dataset_processing/gpt4omini_batch_few_shot",
        "batch_id": None,
        "status": "pending",
        "cost": 0.03,
    },
    {
        "name": "chain_of_thought",
        "description": "Chain-of-thought reasoning (identify sections first)",
        "task": "image_to_dwc_cot",
        "output_dir": "full_dataset_processing/gpt4omini_batch_cot",
        "batch_id": None,
        "status": "pending",
        "cost": 0.03,
    },
    {
        "name": "ocr_first",
        "description": "Two-pass OCR strategy (extract text, then structure)",
        "task": "image_to_dwc_ocr_first",
        "output_dir": "full_dataset_processing/gpt4omini_batch_ocr_first",
        "batch_id": None,
        "status": "pending",
        "cost": 0.03,
    },
]


def save_experiments(experiments: List[Dict], filepath: Path = Path("experiments.json")):
    """Save experiment state to JSON."""
    with open(filepath, "w") as f:
        json.dump(
            {"last_updated": datetime.now().isoformat(), "experiments": experiments}, f, indent=2
        )
    print(f"💾 Saved experiment state: {filepath}")


def load_experiments(filepath: Path = Path("experiments.json")) -> List[Dict]:
    """Load experiment state from JSON."""
    if not filepath.exists():
        return EXPERIMENTS

    with open(filepath, "r") as f:
        data = json.load(f)

    return data["experiments"]


def submit_batch(experiment: Dict) -> str:
    """Submit a single batch experiment."""
    print(f"\n{'=' * 70}")
    print(f"SUBMITTING: {experiment['name']}")
    print(f"Description: {experiment['description']}")
    print(f"{'=' * 70}")

    # Create batch request
    cmd_create = [
        "uv",
        "run",
        "python",
        "scripts/create_batch_request.py",
        "--input",
        "/tmp/imgcache",
        "--output",
        experiment["output_dir"],
        "--limit",
        "10",
        "--task",
        experiment["task"],
        "--prompt-dir",
        "config/prompts",
    ]

    print("📋 Creating batch request...")
    result = subprocess.run(cmd_create, capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ Error creating batch request:")
        print(result.stderr)
        return None

    print(result.stdout)

    # Submit batch
    batch_input = Path(experiment["output_dir"]) / "batch_input.jsonl"
    cmd_submit = ["uv", "run", "python", "scripts/submit_batch.py", "--input", str(batch_input)]

    print("📤 Submitting to OpenAI Batch API...")
    result = subprocess.run(cmd_submit, capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ Error submitting batch:")
        print(result.stderr)
        return None

    print(result.stdout)

    # Extract batch ID from output
    batch_id_file = Path(experiment["output_dir"]) / "batch_id.txt"
    with open(batch_id_file, "r") as f:
        batch_id = f.read().strip()

    print(f"✅ Submitted: {batch_id}")
    return batch_id


def submit_all_experiments():
    """Submit all pending experiments in parallel."""
    experiments = load_experiments()

    print("=" * 70)
    print("EXPERIMENT ORCHESTRATOR - PARALLEL BATCH SUBMISSION")
    print("=" * 70)

    pending = [e for e in experiments if e["status"] == "pending"]

    if not pending:
        print("\n✅ All experiments already submitted!")
        print_status(experiments)
        return

    print(f"\n📊 Found {len(pending)} pending experiments:")
    for exp in pending:
        print(f"   - {exp['name']}: {exp['description']}")

    total_cost = sum(e["cost"] for e in pending)
    print(f"\n💰 Total cost for pending experiments: ${total_cost:.2f}")

    # Submit each experiment
    for exp in pending:
        batch_id = submit_batch(exp)

        if batch_id:
            exp["batch_id"] = batch_id
            exp["status"] = "submitted"
            exp["submitted_at"] = datetime.now().isoformat()
        else:
            exp["status"] = "failed"

        # Save after each submission
        save_experiments(experiments)

    print(f"\n{'=' * 70}")
    print("📤 BATCH SUBMISSION COMPLETE")
    print(f"{'=' * 70}")
    print_status(experiments)


def print_status(experiments: List[Dict] = None):
    """Print status of all experiments."""
    if experiments is None:
        experiments = load_experiments()

    print(f"\n{'=' * 70}")
    print("EXPERIMENT STATUS")
    print(f"{'=' * 70}\n")

    client = OpenAI()

    for exp in experiments:
        print(f"📋 {exp['name']}")
        print(f"   Description: {exp['description']}")
        print(f"   Task: {exp['task']}")
        print(f"   Cost: ${exp['cost']:.2f}")

        if exp["batch_id"]:
            print(f"   Batch ID: {exp['batch_id']}")

            try:
                batch = client.batches.retrieve(exp["batch_id"])
                print(f"   Status: {batch.status}")

                if batch.request_counts:
                    total = batch.request_counts.total
                    completed = batch.request_counts.completed
                    failed = batch.request_counts.failed

                    if total > 0:
                        progress = completed / total * 100
                        print(f"   Progress: {completed}/{total} ({progress:.0f}%)")
                        if failed > 0:
                            print(f"   ⚠️  Failed: {failed}")
            except Exception as e:
                print(f"   ⚠️  Error checking status: {e}")
        else:
            print(f"   Status: {exp['status']}")

        print()


def compare_experiments():
    """Compare results from all completed experiments."""
    experiments = load_experiments()

    print(f"\n{'=' * 70}")
    print("EXPERIMENT COMPARISON")
    print(f"{'=' * 70}\n")

    completed = []
    client = OpenAI()

    for exp in experiments:
        if not exp["batch_id"]:
            continue

        try:
            batch = client.batches.retrieve(exp["batch_id"])

            if batch.status == "completed":
                completed.append(
                    {"name": exp["name"], "description": exp["description"], "batch": batch}
                )
        except Exception as e:
            print(f"⚠️  Error checking {exp['name']}: {e}")

    if not completed:
        print("⏳ No completed experiments yet. Check back later!")
        print("\nRun: python scripts/experiment_orchestrator.py --status")
        return

    print(f"✅ Found {len(completed)} completed experiments\n")

    for result in completed:
        batch = result["batch"]
        print(f"📊 {result['name']}")
        print(f"   Description: {result['description']}")
        print(f"   Total requests: {batch.request_counts.total}")
        print(f"   Completed: {batch.request_counts.completed}")
        print(f"   Failed: {batch.request_counts.failed}")
        print()

    print("💡 Next steps:")
    print("   1. Download results:")
    print("      python scripts/process_batch_results.py --batch-id <id>")
    print("   2. Run validation comparison:")
    print("      python scripts/compare_extractions.py")


def main():
    parser = argparse.ArgumentParser(description="Orchestrate parallel batch experiments")
    parser.add_argument("--submit", action="store_true", help="Submit all pending experiments")
    parser.add_argument("--status", action="store_true", help="Check status of all experiments")
    parser.add_argument(
        "--compare", action="store_true", help="Compare results from completed experiments"
    )

    args = parser.parse_args()

    if args.submit:
        submit_all_experiments()
    elif args.status:
        print_status()
    elif args.compare:
        compare_experiments()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
