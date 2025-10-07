#!/usr/bin/env python
"""Quick batch status checker for testing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from batch_monitor import BatchMonitorEngine

# Initialize engine
engine = BatchMonitorEngine()

# Check both v2 batches
batch_ids = [
    "batch_68e588743e2c8190a7d6e429c1ac3cc4",  # Few-Shot v2
    "batch_68e5888230288190a6702f4b50998888",  # CoT v2
]

print("📊 Batch Status Check\n")

for batch_id in batch_ids:
    try:
        status = engine.fetch_status(batch_id)
        print(f"{status.status_emoji} {batch_id[:24]}...")
        print(f"   Status: {status.status}")
        print(f"   Progress: {status.progress.completed}/{status.progress.total} ({status.progress.completion_percentage:.0f}%)")
        print(f"   Elapsed: {status.timing.elapsed_minutes:.1f} min")
        if status.completion_eta_seconds:
            print(f"   ETA: ~{status.completion_eta_seconds / 60:.1f} min")
        if status.output_file_id:
            print(f"   Output: {status.output_file_id}")
        print()
    except Exception as e:
        print(f"❌ Error checking {batch_id[:24]}: {e}\n")
