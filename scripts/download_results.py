#!/usr/bin/env python
"""Download batch results from OpenAI."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from openai import OpenAI

if len(sys.argv) < 3:
    print("Usage: python download_results.py <batch_id> <output_file>")
    sys.exit(1)

batch_id = sys.argv[1]
output_file = Path(sys.argv[2])

client = OpenAI()

# Get batch info
batch = client.batches.retrieve(batch_id)

if batch.status != "completed":
    print(f"❌ Batch not complete yet. Status: {batch.status}")
    sys.exit(1)

if not batch.output_file_id:
    print("❌ No output file available")
    sys.exit(1)

# Download results
print(f"📥 Downloading results from {batch.output_file_id}...")
content = client.files.content(batch.output_file_id)

# Write to file
output_file.write_bytes(content.read())
print(f"✅ Results saved to {output_file}")
print(f"   Size: {output_file.stat().st_size / 1024:.1f} KB")
