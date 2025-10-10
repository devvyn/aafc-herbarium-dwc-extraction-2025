#!/usr/bin/env python3
"""Interactive validation tool for herbarium specimens."""

import json
import subprocess
from pathlib import Path

# Load validation samples
samples_file = "full_dataset_processing/run_20251005_151758/validation_samples.jsonl"
samples = [json.loads(line) for line in open(samples_file)]

# Load fuzzy candidates
fuzzy_file = "full_dataset_processing/run_20251005_151758/fuzzy_match_candidates.jsonl"
fuzzy_map = {}
for line in open(fuzzy_file):
    item = json.loads(line)
    fuzzy_map[item["sha256"]] = item

# Load or create validation results
results_file = "full_dataset_processing/run_20251005_151758/human_validation.jsonl"
validated = set()
if Path(results_file).exists():
    validated = {json.loads(line)["sha256"] for line in open(results_file)}

print(f"\n{'='*70}")
print("AAFC Herbarium Interactive Validation Tool")
print(f"{'='*70}")
print(f"Total samples: {len(samples)}")
print(f"Already validated: {len(validated)}")
print(f"Remaining: {len(samples) - len(validated)}")
print(f"{'='*70}\n")

# Filter to high-quality samples first
high_quality = [
    s for s in samples if s["quality_tier"] == "high_quality" and s["sha256"] not in validated
]

print(f"Starting with HIGH QUALITY samples ({len(high_quality)} remaining)\n")

for i, record in enumerate(high_quality[:5], 1):  # Start with 5
    sha = record["sha256"]
    sha_short = sha[:16]
    dwc = record["dwc"]

    print(f"\n{'='*70}")
    print(f"Sample {i}/5: {sha_short}...")
    print(f"{'='*70}")

    # Show image
    img_path = f"/tmp/imgcache/{sha}.jpg"
    print(f"\nOpening image: {img_path}")
    subprocess.run(["open", img_path], check=False)

    # Show extracted data
    print("\n📋 EXTRACTED DATA:")
    for field in [
        "catalogNumber",
        "scientificName",
        "eventDate",
        "recordedBy",
        "locality",
        "stateProvince",
        "country",
    ]:
        value = dwc.get(field, "")
        conf = record["dwc_confidence"].get(field, 0)
        status = "✓" if value else "✗"
        print(f"  {status} {field:20s}: {value:50s} (conf: {conf:.2f})")

    # Show fuzzy matches if available
    if sha in fuzzy_map:
        print("\n🔍 FUZZY MATCH SUGGESTIONS:")
        for match in fuzzy_map[sha]["matches"][:3]:
            print(f"  → {match['reference']:40s} (similarity: {match['similarity']:.2f})")

    print(f"\n{'='*70}")
    print("VALIDATION OPTIONS:")
    print("  [c] Correct - extraction is good")
    print("  [w] Wrong - extraction has errors (will prompt for corrections)")
    print("  [s] Skip - come back later")
    print("  [q] Quit - save and exit")
    print(f"{'='*70}")

    choice = input("\nYour choice: ").strip().lower()

    if choice == "q":
        print("\nSaving and exiting...")
        break
    elif choice == "s":
        print("Skipped.")
        continue
    elif choice == "c":
        # Mark as correct
        validation_record = {
            "sha256": sha,
            "validation_status": "correct",
            "extracted": dwc,
            "corrected": None,
        }
        with open(results_file, "a") as f:
            f.write(json.dumps(validation_record) + "\n")
        print("✓ Marked as correct")
    elif choice == "w":
        # Collect corrections
        print("\nEnter corrections (press Enter to keep extracted value):")
        corrected = {}
        for field in ["catalogNumber", "scientificName", "eventDate", "recordedBy", "locality"]:
            current = dwc.get(field, "")
            prompt = f"  {field} [{current}]: "
            new_value = input(prompt).strip()
            corrected[field] = new_value if new_value else current

        validation_record = {
            "sha256": sha,
            "validation_status": "corrected",
            "extracted": dwc,
            "corrected": corrected,
        }
        with open(results_file, "a") as f:
            f.write(json.dumps(validation_record) + "\n")
        print("✓ Corrections saved")

print(f"\n{'='*70}")
print("Validation session complete!")
print(f"Results saved to: {results_file}")
print(f"{'='*70}\n")
