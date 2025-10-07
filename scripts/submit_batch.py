#!/usr/bin/env python
"""
Submit OpenAI Batch API Job

Uploads batch request file and creates a batch job for herbarium extraction.
Saves batch ID for monitoring and result retrieval.

Usage:
    python scripts/submit_batch.py --input full_dataset_processing/gpt4omini_batch/batch_input.jsonl

Output:
    - batch_id.txt (batch job ID for monitoring)
    - batch_info.json (complete batch metadata)
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file
except ImportError:
    pass  # dotenv optional, environment may already be set

try:
    from openai import OpenAI
except ImportError:
    print("Error: OpenAI SDK not installed")
    print("Install with: uv add openai")
    sys.exit(1)


def submit_batch(input_file: Path, endpoint: str = "/v1/chat/completions") -> dict:
    """Submit batch job to OpenAI.

    Args:
        input_file: Path to batch input JSONL file
        endpoint: OpenAI API endpoint

    Returns:
        Batch object dict with id, status, etc.
    """
    client = OpenAI()

    print(f"📤 Uploading batch input file...")
    print(f"   File: {input_file}")
    print(f"   Size: {input_file.stat().st_size / 1024 / 1024:.1f} MB")

    # Upload file
    with open(input_file, "rb") as f:
        file_obj = client.files.create(
            file=f,
            purpose="batch"
        )

    print(f"✅ File uploaded: {file_obj.id}")

    # Create batch job
    print(f"\n📋 Creating batch job...")
    batch = client.batches.create(
        input_file_id=file_obj.id,
        endpoint=endpoint,
        completion_window="24h"
    )

    print(f"✅ Batch job created:")
    print(f"   Batch ID: {batch.id}")
    print(f"   Status: {batch.status}")
    print(f"   Endpoint: {batch.endpoint}")
    print(f"   Completion window: {batch.completion_window}")

    return batch


def save_batch_info(batch: dict, output_dir: Path):
    """Save batch information to files.

    Args:
        batch: Batch object dict
        output_dir: Directory to save batch info
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save batch ID
    batch_id_file = output_dir / "batch_id.txt"
    with open(batch_id_file, "w") as f:
        f.write(batch.id)

    print(f"\n💾 Saved batch ID:")
    print(f"   {batch_id_file}")

    # Save complete batch info
    batch_info_file = output_dir / "batch_info.json"
    batch_dict = {
        "id": batch.id,
        "object": batch.object,
        "endpoint": batch.endpoint,
        "errors": batch.errors,
        "input_file_id": batch.input_file_id,
        "completion_window": batch.completion_window,
        "status": batch.status,
        "output_file_id": batch.output_file_id,
        "error_file_id": batch.error_file_id,
        "created_at": batch.created_at,
        "in_progress_at": batch.in_progress_at,
        "expires_at": batch.expires_at,
        "finalizing_at": batch.finalizing_at,
        "completed_at": batch.completed_at,
        "failed_at": batch.failed_at,
        "expired_at": batch.expired_at,
        "cancelling_at": batch.cancelling_at,
        "cancelled_at": batch.cancelled_at,
        "request_counts": {
            "total": batch.request_counts.total,
            "completed": batch.request_counts.completed,
            "failed": batch.request_counts.failed
        } if batch.request_counts else None,
        "metadata": batch.metadata,
        "submitted_at": datetime.now().isoformat(),
    }

    with open(batch_info_file, "w") as f:
        json.dump(batch_dict, f, indent=2)

    print(f"   {batch_info_file}")


def estimate_completion(batch: dict):
    """Print estimated completion time.

    Args:
        batch: Batch object dict
    """
    now = datetime.now()

    if batch.expires_at:
        expires = datetime.fromtimestamp(batch.expires_at)
        time_until = expires - now

        print(f"\n⏱️  Estimated completion:")
        print(f"   Submitted: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Expires: {expires.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Time remaining: {time_until.total_seconds() / 3600:.1f} hours")
        print(f"\n💡 Tip: Most batches complete in 12-20 hours, not the full 24 hours")
    else:
        # Fallback estimate
        estimated = now + timedelta(hours=18)
        print(f"\n⏱️  Estimated completion:")
        print(f"   Submitted: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Estimated: {estimated.strftime('%Y-%m-%d %H:%M:%S')} (18 hours)")


def main():
    parser = argparse.ArgumentParser(
        description="Submit OpenAI Batch API job for herbarium extraction"
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Batch input JSONL file"
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        default="/v1/chat/completions",
        help="OpenAI API endpoint"
    )

    args = parser.parse_args()

    # Validate input
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    # Determine output directory
    output_dir = args.input.parent

    print("=" * 70)
    print("OPENAI BATCH API SUBMISSION")
    print("=" * 70)

    try:
        # Submit batch
        batch = submit_batch(args.input, args.endpoint)

        # Save batch info
        save_batch_info(batch, output_dir)

        # Show completion estimate
        estimate_completion(batch)

        # Next steps
        print("\n" + "=" * 70)
        print("📤 BATCH SUBMITTED SUCCESSFULLY")
        print("=" * 70)
        print(f"\n📋 Batch ID: {batch.id}")
        print(f"📊 Total requests: {batch.request_counts.total if batch.request_counts else 'N/A'}")
        print(f"\n📍 Next steps:")
        print(f"   1. Monitor progress:")
        print(f"      python scripts/monitor_batch.py --batch-id {batch.id}")
        print(f"\n   2. Or check status manually:")
        print(f"      python -c \"from openai import OpenAI; print(OpenAI().batches.retrieve('{batch.id}').status)\"")
        print(f"\n   3. When complete, process results:")
        print(f"      python scripts/process_batch_results.py --batch-id {batch.id}")

        # Cost estimate
        if batch.request_counts and batch.request_counts.total:
            # GPT-4o-mini pricing: $0.150/1M input tokens, $0.600/1M output tokens
            # Batch API: 50% discount
            # Rough estimate: ~5K input tokens/image, ~1K output tokens
            est_input_tokens = batch.request_counts.total * 5000
            est_output_tokens = batch.request_counts.total * 1000

            est_cost = (est_input_tokens / 1_000_000 * 0.150 * 0.5) + \
                      (est_output_tokens / 1_000_000 * 0.600 * 0.5)

            print(f"\n💰 Estimated cost: ${est_cost:.2f} (50% batch discount)")
            print(f"   (Regular API would cost: ${est_cost * 2:.2f})")

    except Exception as e:
        print(f"\n❌ Error submitting batch: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
