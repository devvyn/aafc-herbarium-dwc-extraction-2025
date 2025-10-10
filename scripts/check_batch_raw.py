#!/usr/bin/env python
"""Get raw batch data from API to debug stuck status."""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from openai import OpenAI

if len(sys.argv) < 2:
    print("Usage: python check_batch_raw.py <batch_id>")
    sys.exit(1)

batch_id = sys.argv[1]
client = OpenAI()

batch = client.batches.retrieve(batch_id)
print(json.dumps(batch.model_dump(), indent=2, default=str))
