#!/usr/bin/env python
"""Cancel a batch job."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from openai import OpenAI

if len(sys.argv) < 2:
    print("Usage: python cancel_batch.py <batch_id>")
    sys.exit(1)

batch_id = sys.argv[1]
client = OpenAI()

print(f"Cancelling {batch_id}...")
batch = client.batches.cancel(batch_id)
print(f"✅ Status: {batch.status}")
