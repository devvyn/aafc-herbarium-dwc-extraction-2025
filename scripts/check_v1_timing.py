#!/usr/bin/env python
"""Check v1 batch actual timing."""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from openai import OpenAI

client = OpenAI()

# Check all v1 batches
v1_batches = [
    ("Few-Shot v1", "batch_68e49bae521481908a0b32643a10537d"),
    ("CoT v1", "batch_68e49cd3f22881908f50d8beaab34732"),
    ("OCR-First v1", "batch_68e49d71fb3c8190a12e9c9dbeb82f01"),
]

for name, batch_id in v1_batches:
    batch = client.batches.retrieve(batch_id)

    print(f"\n=== {name} ===")
    print(f"Status: {batch.status}")
    print(f"Created: {datetime.fromtimestamp(batch.created_at)}")

    if batch.in_progress_at:
        print(f"Started: {datetime.fromtimestamp(batch.in_progress_at)}")

    if batch.completed_at:
        print(f"Completed: {datetime.fromtimestamp(batch.completed_at)}")
        duration = batch.completed_at - batch.in_progress_at if batch.in_progress_at else 0
        print(f"⏱️  Duration: {duration / 60:.1f} minutes ({duration} seconds)")

    print(f"Requests: {batch.request_counts.completed}/{batch.request_counts.total}")
