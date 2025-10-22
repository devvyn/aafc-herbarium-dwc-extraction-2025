# Specimen Provenance Architecture (v2.0.0)

## Overview

The specimen provenance system provides complete lineage tracking for herbarium specimens from raw images through all extraction runs and transformations. This architecture enables reproducible research, iterative quality improvement, and production-ready data management.

**Key Innovation**: Shift from image-centric to specimen-centric data model with automatic deduplication and multi-extraction aggregation.

## Core Concepts

### 1. Specimen Identity Preservation

**Problem**: Previous versions lost specimen identity after extraction
- Multiple images of same specimen treated independently
- No way to aggregate results from multiple extraction attempts
- Difficult to track provenance through pipeline

**Solution**: Content-addressed specimen tracking
```python
specimen_id = sha256(image_content)  # Immutable specimen identifier
extraction_id = sha256(image_sha256 + extraction_params)  # Unique extraction
```

### 2. Deduplication Strategy

**Automatic deduplication at two levels:**

**Level 1: Image deduplication**
- SHA256 hash identifies unique specimen images
- Same image processed multiple times → same specimen_id
- Handles file renaming, copies, duplicates

**Level 2: Extraction deduplication**
```python
extraction_params = {
    "model": "gpt-4o-mini",
    "prompt_version": "v2.1",
    "ocr_engine": "apple_vision",
    "timestamp": "2025-10-22T12:00:00Z"
}

# Dedup key: (image_sha256, extraction_params_hash)
# Multiple identical extractions → single stored result
```

## Database Schema

### Core Tables

#### `specimens`
```sql
CREATE TABLE specimens (
    specimen_id TEXT PRIMARY KEY,  -- SHA256 of image content
    first_seen_at TIMESTAMP,
    image_filename TEXT,
    image_path TEXT,
    image_size_bytes INTEGER,
    image_sha256 TEXT UNIQUE,
    s3_key TEXT,  -- Content-addressed S3 storage
    metadata_json TEXT  -- Capture metadata, EXIF, etc.
);
```

#### `extraction_runs`
```sql
CREATE TABLE extraction_runs (
    extraction_id TEXT PRIMARY KEY,  -- SHA256(specimen_id + params)
    specimen_id TEXT REFERENCES specimens(specimen_id),
    extraction_params_json TEXT,  -- Model, prompt, OCR engine
    extracted_at TIMESTAMP,
    git_commit_sha TEXT,  -- Code version used
    extracted_fields_json TEXT,  -- Raw extraction results
    confidence_scores_json TEXT,  -- Per-field confidence
    processing_time_seconds REAL
);
```

#### `specimen_aggregations`
```sql
CREATE TABLE specimen_aggregations (
    specimen_id TEXT PRIMARY KEY REFERENCES specimens(specimen_id),
    aggregated_at TIMESTAMP,
    extraction_count INTEGER,  -- How many runs aggregated
    candidate_fields_json TEXT,  -- All candidate values per field
    best_candidates_json TEXT,  -- Highest confidence per field
    review_status TEXT,  -- pending, approved, rejected
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,
    review_notes TEXT
);
```

#### `data_quality_flags`
```sql
CREATE TABLE data_quality_flags (
    flag_id INTEGER PRIMARY KEY AUTOINCREMENT,
    specimen_id TEXT REFERENCES specimens(specimen_id),
    flag_type TEXT,  -- MISSING_FIELD, LOW_CONFIDENCE, DUPLICATE_CATALOG
    severity TEXT,  -- error, warning, info
    message TEXT,
    created_at TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution_notes TEXT
);
```

## Data Flow

### 1. Specimen Registration

```python
from src.provenance.specimen_index import SpecimenIndex

index = SpecimenIndex("specimen_index.db")

# Register specimen from image
specimen_id = index.register_specimen(
    image_path="photos/specimen_001.jpg",
    metadata={"collection": "AAFC-SRDC", "batch": "2025-09"}
)
# Returns: "a1b2c3d4..." (SHA256 of image content)
```

### 2. Recording Extractions

```python
# Run extraction
extraction_params = {
    "model": "gpt-4o-mini",
    "prompt_version": "v2.1",
    "ocr_engine": "apple_vision"
}

extracted_fields = {
    "scientificName": "Bouteloua gracilis",
    "catalogNumber": "019121",
    "eventDate": "1969-08-14",
    # ... more fields
}

confidence_scores = {
    "scientificName": 0.95,
    "catalogNumber": 0.88,
    "eventDate": 0.92
}

# Record extraction (automatically deduplicates)
extraction_id = index.record_extraction(
    specimen_id=specimen_id,
    extraction_params=extraction_params,
    extracted_fields=extracted_fields,
    confidence_scores=confidence_scores,
    git_commit_sha="6a372ca"
)
```

### 3. Multi-Extraction Aggregation

```python
# Aggregate all extractions for a specimen
aggregation = index.aggregate_specimen_extractions(specimen_id)

# Returns:
{
    "specimen_id": "a1b2c3d4...",
    "extraction_count": 3,  # Ran 3 different extraction attempts

    # All candidate values per field
    "candidate_fields": {
        "scientificName": [
            {"value": "Bouteloua gracilis", "confidence": 0.95, "extraction_id": "..."},
            {"value": "Bouteloua gracilis (HBK.) Lag.", "confidence": 0.92, "extraction_id": "..."},
            {"value": "Bouteloua gracilis", "confidence": 0.88, "extraction_id": "..."}
        ],
        "catalogNumber": [
            {"value": "019121", "confidence": 0.88, "extraction_id": "..."},
            {"value": "19121", "confidence": 0.75, "extraction_id": "..."}
        ]
    },

    # Best candidate per field (highest confidence)
    "best_candidates": {
        "scientificName": {
            "value": "Bouteloua gracilis",
            "confidence": 0.95,
            "extraction_id": "...",
            "agreement_count": 2  # 2 of 3 extractions agreed
        },
        "catalogNumber": {
            "value": "019121",
            "confidence": 0.88,
            "extraction_id": "...",
            "agreement_count": 1
        }
    }
}
```

### 4. Quality Flagging

```python
# Automatic quality flag generation
flags = index.generate_quality_flags(specimen_id)

# Example flags:
[
    {
        "flag_type": "LOW_CONFIDENCE_FIELD",
        "severity": "warning",
        "message": "catalogNumber confidence (0.88) below threshold (0.90)"
    },
    {
        "flag_type": "MISSING_REQUIRED_FIELD",
        "severity": "error",
        "message": "Required field 'locality' not extracted"
    },
    {
        "flag_type": "DISAGREEMENT_BETWEEN_EXTRACTIONS",
        "severity": "warning",
        "message": "catalogNumber has conflicting values: '019121' vs '19121'"
    }
]
```

## Review Workflow Integration

### 1. Queue Specimens for Review

```python
# Get specimens needing review (sorted by priority)
review_queue = index.get_review_queue(
    limit=50,
    min_confidence=0.0,  # Include low confidence
    has_flags=True  # Prioritize flagged specimens
)

# Returns specimens with:
# - All candidate fields
# - Quality flags
# - Aggregation statistics
# - Original images (via specimen_id)
```

### 2. Human Review Process

```python
# Curator reviews specimen in web interface
# - Sees all candidate values
# - Sees confidence scores
# - Sees quality flags
# - Can accept, reject, or edit fields

# Record review decision
index.record_review(
    specimen_id=specimen_id,
    status="approved",
    reviewed_by="curator@example.com",
    final_fields={
        "scientificName": "Bouteloua gracilis (HBK.) Lag.",  # Edited
        "catalogNumber": "019121",  # Accepted best candidate
        "eventDate": "1969-08-14"  # Accepted
    },
    notes="Added authority to scientific name"
)
```

### 3. Progressive Publication

```python
# Export approved specimens only
approved = index.export_approved_specimens(
    format="darwin_core",
    version="v2.0.0-draft"
)

# Export by review batch
batch_1 = index.export_by_review_batch(
    reviewed_after="2025-10-01",
    reviewed_before="2025-10-07",
    status="approved"
)

# Export with full provenance
full_export = index.export_with_provenance(
    include_extraction_history=True,
    include_quality_flags=True,
    include_review_audit=True
)
```

## Migration from v1.x

### Safe Migration Strategy

**Phase 1: Populate Specimen Index**
```bash
# Migrate existing v1.x extraction data
python scripts/migrate_to_specimen_index.py \
    --input full_dataset_processing/run_20250930_181456/raw.jsonl \
    --output specimen_index.db \
    --dry-run  # Test first
```

**Phase 2: Verify Migration**
```python
# Compare v1.x and v2.0 outputs
verification = compare_migrations(
    v1_path="raw.jsonl",
    v2_db="specimen_index.db"
)

# Should show:
# - All specimens migrated
# - No data loss
# - Confidence scores preserved
```

**Phase 3: Progressive Cutover**
- Keep v1.x data as read-only archive
- New extractions → v2.0 specimen index
- Gradual review and approval in v2.0 system

## Benefits

### 1. Reproducibility
- Complete provenance from image to publication
- Git commit tracking for code versions
- Immutable specimen identifiers
- Audit trail for all transformations

### 2. Quality Improvement
- Multi-extraction aggregation increases accuracy
- Confidence-weighted candidate selection
- Automatic quality flag generation
- Systematic review workflow

### 3. Data Management
- Automatic deduplication
- Efficient storage (no duplicate extractions)
- Content-addressed S3 integration
- Rollback capability via provenance

### 4. Research Enablement
- Compare extraction methods
- A/B testing of models
- Iterative improvement tracking
- Publication-ready datasets

## Future Enhancements (v2.1.0+)

### GBIF Validation Integration
- Automatic pre-validation during aggregation
- Taxonomy verification via GBIF API
- Locality verification (coordinate validation)
- Quality flags for GBIF issues

### Advanced Aggregation
- Ensemble voting across models
- Weighted confidence by model performance
- Field-specific model selection
- Dynamic prompt optimization

### Collaborative Review
- Multi-reviewer consensus tracking
- Review assignment and routing
- Inter-reviewer agreement metrics
- Specialized review workflows (taxonomy, geography, etc.)

## Technical Implementation

### Performance Considerations
- **Indexing**: B-tree indexes on specimen_id, extraction_id
- **Caching**: LRU cache for frequent specimen lookups
- **Batch operations**: Bulk insert for large migration
- **Incremental aggregation**: Update only changed specimens

### Storage Efficiency
- **Deduplication**: ~60% reduction in storage for typical workflows
- **JSON compression**: gzip for large JSON fields
- **S3 integration**: Content-addressed, immutable image storage
- **Pruning**: Archive old extraction runs (keep provenance metadata)

## Related Documentation

- **Release Plan**: [RELEASE_2_0_PLAN.md](RELEASE_2_0_PLAN.md)
- **GBIF Integration**: [GBIF_VALIDATION_INTEGRATION.md](GBIF_VALIDATION_INTEGRATION.md) (v2.1.0)
- **Scientific Provenance Pattern**: [SCIENTIFIC_PROVENANCE_PATTERN.md](SCIENTIFIC_PROVENANCE_PATTERN.md)
- **Migration Guide**: `scripts/migrate_to_specimen_index.py --help`

## Summary

The v2.0.0 specimen provenance architecture transforms the herbarium digitization pipeline from a one-off extraction tool into a production-ready data management system with:

✅ Complete specimen lineage tracking
✅ Automatic deduplication and aggregation
✅ Quality-driven review workflows
✅ Progressive publication capability
✅ Full reproducibility and audit trails

This foundation enables scientific-grade digitization at institutional scale.
