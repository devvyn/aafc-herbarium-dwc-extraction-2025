#!/usr/bin/env python3
"""Analyze gpt-4o-mini extraction accuracy against ground truth."""

import json
from pathlib import Path
from difflib import SequenceMatcher

# Load ground truth validations
validation_file = Path("full_dataset_processing/run_20251005_151758/human_validation.jsonl")
validations = [json.loads(line) for line in open(validation_file)]

# Load gpt-4o-mini extractions
gpt4omini_file = Path("full_dataset_processing/gpt4omini_test/raw.jsonl")
extractions = {json.loads(line)['sha256']: json.loads(line) for line in open(gpt4omini_file)}

print("="*70)
print("GPT-4o-mini Accuracy Analysis")
print("="*70)
print(f"Ground truth specimens: {len(validations)}")
print(f"Extracted specimens: {len(extractions)}")
print()

# Field-by-field accuracy
fields = [
    'catalogNumber', 'scientificName', 'eventDate', 'recordedBy',
    'locality', 'habitat', 'recordNumber', 'country',
    'stateProvince', 'county', 'identifiedBy', 'minimumElevationInMeters'
]

field_stats = {f: {'exact': 0, 'partial': 0, 'missing': 0, 'total': 0} for f in fields}

exact_matches = 0
partial_matches = 0

def similarity(a, b):
    """Calculate similarity ratio between two strings."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()

# Analyze each validation
for val in validations:
    sha = val['sha256']
    ground_truth = val['corrected'] or val['extracted']

    if sha not in extractions:
        print(f"WARNING: {sha} not found in extractions")
        continue

    extracted = extractions[sha].get('dwc', {})

    # Check each field
    field_match_count = 0
    for field in fields:
        gt_value = ground_truth.get(field, '').strip()
        ex_value = extracted.get(field, {}).get('value', '').strip()

        if not gt_value and not ex_value:
            continue  # Both empty, skip

        field_stats[field]['total'] += 1

        if gt_value == ex_value:
            field_stats[field]['exact'] += 1
            field_match_count += 1
        elif similarity(gt_value, ex_value) >= 0.7:
            field_stats[field]['partial'] += 1
        else:
            field_stats[field]['missing'] += 1

    if field_match_count == len([f for f in fields if ground_truth.get(f)]):
        exact_matches += 1
    elif field_match_count > 0:
        partial_matches += 1

print("OVERALL ACCURACY")
print("-" * 70)
print(f"Exact specimen matches: {exact_matches}/{len(validations)} ({exact_matches/len(validations)*100:.1f}%)")
print(f"Partial matches: {partial_matches}/{len(validations)} ({partial_matches/len(validations)*100:.1f}%)")
print()

print("FIELD-BY-FIELD ACCURACY")
print("-" * 70)
print(f"{'Field':<25} {'Exact':<10} {'Partial':<10} {'Missing':<10} {'Total':<10} {'Accuracy':<10}")
print("-" * 70)

for field in fields:
    stats = field_stats[field]
    if stats['total'] > 0:
        accuracy = (stats['exact'] / stats['total']) * 100
        print(f"{field:<25} {stats['exact']:<10} {stats['partial']:<10} {stats['missing']:<10} {stats['total']:<10} {accuracy:.1f}%")

print()
print("="*70)

# Show a few examples
print("\nSAMPLE COMPARISONS (first 3 specimens)")
print("="*70)

for i, val in enumerate(validations[:3]):
    sha = val['sha256']
    ground_truth = val['corrected'] or val['extracted']
    extracted = extractions[sha].get('dwc', {})

    print(f"\nSpecimen {i+1}: {sha[:12]}...")
    print("-" * 70)

    for field in ['catalogNumber', 'scientificName', 'eventDate', 'recordedBy', 'locality']:
        gt = ground_truth.get(field, '')
        ex = extracted.get(field, {}).get('value', '')
        match = "✓" if gt == ex else "✗"

        print(f"{match} {field}:")
        print(f"  Ground truth: {gt}")
        print(f"  Extracted:    {ex}")
