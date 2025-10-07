#!/usr/bin/env python
"""Check v2 batch detailed status."""

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

v2_batches = [
    ("Few-Shot v2", "batch_68e588743e2c8190a7d6e429c1ac3cc4"),
    ("CoT v2", "batch_68e5888230288190a6702f4b50998888"),
]

for name, batch_id in v2_batches:
    batch = client.batches.retrieve(batch_id)

    print(f"\n=== {name} ===")
    print(f"Status: {batch.status}")
    print(f"Created: {datetime.fromtimestamp(batch.created_at)}")

    if batch.in_progress_at:
        print(f"Started: {datetime.fromtimestamp(batch.in_progress_at)}")
        elapsed = (datetime.now().timestamp() - batch.in_progress_at) / 60
        print(f"⏱️  Time in progress: {elapsed:.1f} minutes")
    else:
        print("⚠️  Not started yet (still in validation queue)")
        elapsed = (datetime.now().timestamp() - batch.created_at) / 60
        print(f"⏱️  Time since creation: {elapsed:.1f} minutes")

    print(f"Requests: {batch.request_counts.completed}/{batch.request_counts.total}")
    print(f"Failed: {batch.request_counts.failed}")
