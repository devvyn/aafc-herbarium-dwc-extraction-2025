#!/usr/bin/env python3
"""Edit validation records to fix typos."""

import json
import sys
from pathlib import Path

validation_file = "full_dataset_processing/run_20251005_151758/human_validation.jsonl"

# Load all records
records = []
for line in open(validation_file):
    records.append(json.loads(line))

print("\n" + "=" * 70)
print("Validation Record Editor")
print("=" * 70)

# Show all records
for i, record in enumerate(records, 1):
    corr = record["corrected"]
    print(f"\n{i}. {record['sha256'][:16]}...")
    print(f"   catalogNumber: {corr['catalogNumber']}")
    print(f"   scientificName: {corr['scientificName']}")
    print(f"   eventDate: {corr['eventDate']}")
    print(f"   recordedBy: {corr['recordedBy']}")
    print(f"   locality: {corr['locality']}")

print("\n" + "=" * 70)
choice = input("\nWhich record to edit? (1-{}, or 'q' to quit): ".format(len(records))).strip()

if choice.lower() == "q":
    print("Exiting without changes.")
    sys.exit(0)

try:
    idx = int(choice) - 1
    if idx < 0 or idx >= len(records):
        print("Invalid record number.")
        sys.exit(1)
except ValueError:
    print("Invalid input.")
    sys.exit(1)

# Edit the selected record
record = records[idx]
corr = record["corrected"]

print(f"\n{'='*70}")
print(f"Editing Record {choice}: {record['sha256'][:16]}...")
print(f"{'='*70}")
print("\nEnter new values (press Enter to keep current value):")

for field in ["catalogNumber", "scientificName", "eventDate", "recordedBy", "locality"]:
    current = corr[field]
    new_value = input(f"  {field} [{current}]: ").strip()
    if new_value:
        corr[field] = new_value

# Save changes
backup_file = validation_file + ".backup"
Path(backup_file).write_text(Path(validation_file).read_text())

with open(validation_file, "w") as f:
    for rec in records:
        f.write(json.dumps(rec) + "\n")

print("\n✅ Changes saved!")
print(f"   Backup created: {backup_file}")
print("\nUpdated values:")
for field in ["catalogNumber", "scientificName", "eventDate", "recordedBy", "locality"]:
    print(f"  {field}: {corr[field]}")
