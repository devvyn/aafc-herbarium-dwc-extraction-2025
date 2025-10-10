#!/usr/bin/env python3
"""Compare Vision API vs GPT-4o-mini on validated specimens with expanded schema v2.0."""

import json
from pathlib import Path
from datetime import datetime

# Load validated specimens
validation_file = Path("full_dataset_processing/run_20251005_151758/human_validation.jsonl")
validations = [json.loads(line) for line in open(validation_file)]

# Get specimen images
image_hashes = [v["sha256"] for v in validations]
image_dir = Path("/tmp/imgcache")

print(f"{'='*70}")
print("Engine Comparison Test - Vision API vs GPT-4o-mini")
print(f"{'='*70}")
print(f"Specimens to test: {len(image_hashes)}")
print("Schema: Darwin Core v2.0 (16 fields)")
print("Prompts: image_to_dwc_v2 (layout-aware)")
print(f"{'='*70}\n")

# Create output directories
output_base = Path("full_dataset_processing/engine_comparison")
output_base.mkdir(parents=True, exist_ok=True)

vision_output = output_base / "vision_results"
gpt4omini_output = output_base / "gpt4omini_results"
vision_output.mkdir(exist_ok=True)
gpt4omini_output.mkdir(exist_ok=True)

# Test Vision API
print("\\n🔬 Testing Vision API with expanded schema...")
print("-" * 70)

# Note: We need to run the actual cli.py commands
# For now, create test manifests

vision_manifest = {
    "test_date": datetime.now().isoformat(),
    "engine": "vision",
    "schema_version": "2.0",
    "prompt_version": "image_to_dwc_v2",
    "specimens": image_hashes,
    "command": f"python cli.py process --input {image_dir} --output {vision_output} --engine vision",
}

gpt4omini_manifest = {
    "test_date": datetime.now().isoformat(),
    "engine": "gpt4omini",
    "schema_version": "2.0",
    "prompt_version": "image_to_dwc_v2",
    "specimens": image_hashes,
    "command": f"python cli.py process --input {image_dir} --output {gpt4omini_output} --engine gpt4omini",
}

(output_base / "vision_manifest.json").write_text(json.dumps(vision_manifest, indent=2))
(output_base / "gpt4omini_manifest.json").write_text(json.dumps(gpt4omini_manifest, indent=2))

print("\\n✅ Test manifests created:")
print(f"   - {output_base}/vision_manifest.json")
print(f"   - {output_base}/gpt4omini_manifest.json")

print("\\n" + "=" * 70)
print("NEXT STEPS:")
print("=" * 70)
print("\\n1. Test Vision API (FREE):")
print(f"   python cli.py process --input {image_dir} --output {vision_output} --engine vision")

print("\\n2. Test GPT-4o-mini ($0.15 per million tokens, ~$0.50 for 20 images):")
print(
    f"   python cli.py process --input {image_dir} --output {gpt4omini_output} --engine gpt4omini"
)

print("\\n3. Compare results:")
print("   python analyze_comparison.py")

print("\\n" + "=" * 70)
