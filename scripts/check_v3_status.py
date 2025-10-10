#!/usr/bin/env python
"""Check v3 batch status."""

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

v3_batches = [
    ("Few-Shot v3", "batch_68e5a1a609488190b7d11e1eae064057"),
    ("CoT v3", "batch_68e5a1b1c6848190aa9b41ad2daefcf6"),
]

print("📊 V3 Batch Status (temperature=0, json_object mode)\n")

for name, batch_id in v3_batches:
    batch = client.batches.retrieve(batch_id)

    print(f"=== {name} ===")
    print(f"Status: {batch.status}")
    print(f"Created: {datetime.fromtimestamp(batch.created_at).strftime('%H:%M:%S')}")

    if batch.in_progress_at:
        started = datetime.fromtimestamp(batch.in_progress_at)
        print(f"Started: {started.strftime('%H:%M:%S')}")
        elapsed = (datetime.now().timestamp() - batch.in_progress_at) / 60
        print(f"⏱️  Time in progress: {elapsed:.1f} minutes")
    else:
        elapsed = (datetime.now().timestamp() - batch.created_at) / 60
        print(f"⏱️  Time validating: {elapsed:.1f} minutes")

    print(f"Requests: {batch.request_counts.completed}/{batch.request_counts.total}")
    print()
