#!/usr/bin/env python3
"""Test Vision API with improved prompts on 20 validated specimens."""

import json
import shutil
from pathlib import Path

print("="*70)
print("Testing Vision API with Expanded Schema v2.0")
print("="*70)

# Load validated specimens
validation_file = Path("full_dataset_processing/run_20251005_151758/human_validation.jsonl")
validations = [json.loads(line) for line in open(validation_file)]

print(f"\n✅ Loaded {len(validations)} validated specimens")

# Create test directory with 20 specimen images
test_dir = Path("test_20_specimens")
test_dir.mkdir(exist_ok=True)

cache_dir = Path("/tmp/imgcache")
copied = 0

for val in validations:
    sha = val['sha256']
    src = cache_dir / f"{sha}.jpg"
    if src.exists():
        dst = test_dir / f"{sha}.jpg"
        if not dst.exists():
            shutil.copy2(src, dst)
            copied += 1

print(f"✅ Copied {copied} images to {test_dir}")

# Create output directory
output_dir = Path("full_dataset_processing/vision_v2_test")
output_dir.mkdir(parents=True, exist_ok=True)

print(f"\n{'='*70}")
print("NEXT STEP: Run extraction with NEW prompts")
print(f"{'='*70}")
print(f"\nCommand:")
print(f"  python cli.py process --input {test_dir} --output {output_dir} --engine vision")

print(f"\n{'='*70}")
print("After running, compare results:")
print(f"{'='*70}")
print(f"  1. OLD extraction: full_dataset_processing/run_20251005_151758/raw.jsonl")
print(f"  2. NEW extraction: {output_dir}/raw.jsonl")
print(f"  3. Ground truth: {validation_file}")
print(f"\nUse: python analyze_vision_improvement.py")

print(f"\n{'='*70}")
print("NOTE: Vision API currently only supports 7 fields via rules engine")
print("For 16-field extraction, you need a GPT model (requires API key)")
print("See: API_SETUP_QUICK.md")
print(f"{'='*70}")
