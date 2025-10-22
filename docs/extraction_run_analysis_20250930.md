# Extraction Run Analysis: run_20250930_181456

## Summary

Analysis of `full_dataset_processing/run_20250930_181456` revealed a combination of issues that resulted in 5,770 entries in `raw.jsonl` for only 2,885 unique specimens.

## Findings

### 1. Duplicate Processing

- **Total extractions**: 5,770
- **Unique specimens**: 2,885
- **Ratio**: Exactly 2.0 (every specimen processed twice)

### 2. All Extractions Failed

**Error**: Missing OpenAI API key

Every single extraction in this run failed with:
```json
{
  "errors": [
    "The api_key client option must be set either by passing api_key to the client or by setting the OPENAI_API_KEY environment variable"
  ],
  "dwc": {}
}
```

**Impact**: 5,770 failed extraction attempts, consuming processing time with zero usable results.

### 3. No Deduplication

The extraction pipeline did not check whether `(image, extraction_params)` combinations had already been processed, allowing the same image to be extracted multiple times with identical parameters.

## Root Causes

1. **Missing environment variable**: `OPENAI_API_KEY` not set during extraction run
2. **No extraction-level deduplication**: System didn't prevent re-processing identical (image, params) combinations
3. **Unknown trigger for duplicate processing**: Unclear why each image was queued twice

## Recommendations

### Implemented Solutions

1. **Specimen Index** (`src/provenance/specimen_index.py`)
   - Tracks specimens through transformations and extraction runs
   - Deduplication at `(image_sha256, params_hash)` level
   - Prevents redundant extraction of identical combinations

2. **Migration Tool** (`scripts/migrate_to_specimen_index.py`)
   - Analyzes existing runs to identify duplicates
   - Populates specimen index from historical data
   - Flags data quality issues

3. **Architecture Documentation** (`docs/specimen_provenance_architecture.md`)
   - Specimen-centric data model
   - Full provenance tracking: original files → transformations → extractions → review
   - Data quality checks for catalog number violations

### Usage

**Check before extraction:**
```python
from src.provenance.specimen_index import SpecimenIndex

index = SpecimenIndex("specimen_index.db")

# Before processing an image:
should_extract, existing_id = index.should_extract(
    image_sha256="000e426d...",
    extraction_params={
        "ocr_engine": "vision",
        "model": "gpt-4o-mini",
        "prompt_version": "v2.1"
    }
)

if not should_extract:
    logger.info(f"Skipping: already extracted ({existing_id})")
    continue

# Proceed with extraction...
```

**Analyze existing runs:**
```bash
python scripts/migrate_to_specimen_index.py \
    --run-dir full_dataset_processing/run_20250930_181456 \
    --index specimen_index.db \
    --analyze-duplicates \
    --check-quality
```

## Benefits

1. **Efficiency**: Eliminate redundant extraction attempts
2. **Cost savings**: Avoid duplicate API calls
3. **Data quality**: Automatic detection of catalog number violations
4. **Provenance**: Full lineage from camera files to final DwC records
5. **Aggregation**: Multiple extraction attempts per specimen contribute to better candidate fields

## Future Work

1. **Original filename mapping**: Link content-addressed images back to camera files (DSC_*.JPG)
2. **Transformation tracking**: Record preprocessing operations in specimen index
3. **Review integration**: Update review UI to show all extraction attempts and data quality flags
4. **Quality gates**: Prevent extraction runs from starting without required API keys

## Related Files

- Architecture: `docs/specimen_provenance_architecture.md`
- Implementation: `src/provenance/specimen_index.py`
- Migration: `scripts/migrate_to_specimen_index.py`
- Monitor TUI: `scripts/monitor_tui.py`
