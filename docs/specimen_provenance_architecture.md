# Specimen-Centric Provenance Architecture

## Overview

This architecture ensures full lineage tracking from physical herbarium specimens through image transformations, extraction runs, and human review, while supporting:

- **Deterministic deduplication**: Avoid re-processing (image, extraction_params) combinations
- **Specimen-level aggregation**: Multiple extractions enrich candidate fields for review
- **Data quality flagging**: Detect violations of expected invariants
- **Full provenance**: Trace final DwC records back to original camera files

## Data Model

### 1. Specimen Identity

**Invariant (expected)**: Physical specimen ↔ camera filename (1:1)

**Reality**: Violations occur and must be flagged

```json
{
  "specimen_id": "DSC_0001",
  "source_identity": {
    "camera_filename": "DSC_0001",
    "expected_catalog_number": "AAFC-12345",
    "sheet_barcode": null,
    "confidence": "assumed"
  },
  "original_files": [
    {
      "path": "original/DSC_0001.JPG",
      "format": "JPEG",
      "dimensions": [6000, 4000],
      "size_bytes": 12345678,
      "sha256": "abc123...",
      "role": "original_photo",
      "captured_at": "2023-06-15T14:30:00Z"
    },
    {
      "path": "original/DSC_0001.NEF",
      "format": "NEF",
      "size_bytes": 23456789,
      "sha256": "def456...",
      "role": "original_raw",
      "captured_at": "2023-06-15T14:30:00Z"
    }
  ],
  "data_quality_flags": []
}
```

### 2. Image Transformations (Provenance DAG)

**Content-addressed derivatives** tracked with lineage:

```json
{
  "sha256": "000e426d...",
  "derived_from": "abc123...",
  "specimen_id": "DSC_0001",
  "transformation": {
    "operation": "resize_for_ocr",
    "params": {
      "target_width": 2000,
      "method": "lanczos",
      "quality": 95
    },
    "timestamp": "2023-06-20T10:00:00Z",
    "tool": "prepare_images_cached.py",
    "tool_version": "1.0.0"
  },
  "file_info": {
    "format": "JPEG",
    "dimensions": [2000, 1333],
    "size_bytes": 456789,
    "stored_at": "s3://bucket/images/00/0e/000e426d...jpg"
  }
}
```

### 3. Extraction Results (Deterministic Cache)

**Deduplication key**: `(image_sha256, extraction_params_hash)`

**Rationale**: Same image + same process = deterministic results

```json
{
  "extraction_id": "uuid-1234",
  "image_sha256": "000e426d...",
  "specimen_id": "DSC_0001",
  "extraction_params": {
    "ocr_engine": "vision",
    "ocr_version": "macos-15.0",
    "model": "gpt-4o-mini",
    "prompt_version": "v2.1",
    "temperature": 0.1,
    "preprocessing": ["grayscale", "deskew"]
  },
  "params_hash": "sha256(extraction_params)",
  "run_id": "2025-10-01T00:16:15",
  "status": "completed",
  "dwc_fields": {
    "catalogNumber": {"value": "AAFC-12345", "confidence": 0.95},
    "scientificName": {"value": "Picea glauca", "confidence": 0.92}
  },
  "raw_jsonl_offset": 42,
  "timestamp": "2025-10-01T00:20:33Z"
}
```

**Deduplication logic**:
```python
def should_process(image_sha256: str, params: dict) -> bool:
    params_hash = hash_extraction_params(params)
    existing = extraction_cache.get(image_sha256, params_hash)
    return existing is None or existing.status == "failed"
```

### 4. Specimen Extraction Aggregation

**Multiple extractions** → **candidate field set** for human review:

```json
{
  "specimen_id": "DSC_0001",
  "extraction_runs": [
    {
      "extraction_id": "uuid-1234",
      "image_sha256": "000e426d...",
      "method": "resize_2000px + gpt4o-mini",
      "timestamp": "2025-10-01T00:20:33Z"
    },
    {
      "extraction_id": "uuid-5678",
      "image_sha256": "111f537e...",
      "method": "grayscale + claude-3.5",
      "timestamp": "2025-10-02T14:15:00Z"
    }
  ],
  "candidate_fields": {
    "catalogNumber": [
      {"value": "AAFC-12345", "confidence": 0.95, "source": "uuid-1234"},
      {"value": "AAFC-12345", "confidence": 0.98, "source": "uuid-5678"}
    ],
    "scientificName": [
      {"value": "Picea glauca", "confidence": 0.92, "source": "uuid-1234"},
      {"value": "Picea glauca", "confidence": 0.89, "source": "uuid-5678"}
    ],
    "locality": [
      {"value": "Near Saskatoon", "confidence": 0.75, "source": "uuid-1234"},
      {"value": "Near Saskatoon, Highway 11 North", "confidence": 0.85, "source": "uuid-5678"}
    ]
  },
  "best_candidates": {
    "catalogNumber": {"value": "AAFC-12345", "confidence": 0.98, "source": "uuid-5678"},
    "scientificName": {"value": "Picea glauca", "confidence": 0.92, "source": "uuid-1234"},
    "locality": {"value": "Near Saskatoon, Highway 11 North", "confidence": 0.85, "source": "uuid-5678"}
  },
  "review_status": "pending",
  "queued_for_review_at": "2025-10-02T14:16:00Z"
}
```

### 5. Human Review & Final Record

```json
{
  "specimen_id": "DSC_0001",
  "reviewed_by": "user@example.com",
  "reviewed_at": "2025-10-03T09:30:00Z",
  "review_decisions": {
    "catalogNumber": {
      "accepted": true,
      "value": "AAFC-12345",
      "source": "uuid-5678",
      "notes": null
    },
    "locality": {
      "accepted": false,
      "value": "Saskatoon, 11km N on Hwy 11",
      "source": "manual_correction",
      "notes": "Corrected for DwC locality format"
    }
  },
  "final_dwc": {
    "catalogNumber": "AAFC-12345",
    "scientificName": "Picea glauca",
    "locality": "Saskatoon, 11km N on Hwy 11",
    "...": "..."
  },
  "status": "approved",
  "exported_to": ["dwca_v1.0.0_20251003.zip"]
}
```

## Data Quality Checks

### Invariant Violations to Flag

1. **Catalog Number Reuse**
   ```python
   # Flag if same catalog number extracted from multiple specimens
   if catalog_num_appears_on_multiple_specimens(cat_num):
       flag_specimen(specimen_id, "DUPLICATE_CATALOG_NUMBER",
                     f"Catalog {cat_num} appears on specimens: {other_specimens}")
   ```

2. **Duplicate Photography**
   ```python
   # Flag if same physical content photographed multiple times
   if image_perceptual_hash_matches_existing(phash):
       flag_specimen(specimen_id, "DUPLICATE_PHOTOGRAPHY",
                     f"Image appears similar to {existing_specimen_id}")
   ```

3. **Malformed Catalog Numbers**
   ```python
   # Flag catalog numbers that don't match expected patterns
   if not matches_pattern(cat_num, r'^AAFC-\d{5,6}$'):
       flag_specimen(specimen_id, "MALFORMED_CATALOG_NUMBER",
                     f"Catalog {cat_num} doesn't match AAFC-##### pattern")
   ```

4. **Incomplete Catalog Numbers**
   ```python
   # Flag partial/unclear catalog numbers
   if extraction_confidence < 0.7 or "?" in cat_num:
       flag_specimen(specimen_id, "INCOMPLETE_CATALOG_NUMBER",
                     f"Catalog {cat_num} extracted with low confidence")
   ```

5. **Missing Critical Fields**
   ```python
   # Flag specimens missing required DwC fields
   required = ["catalogNumber", "scientificName", "recordedBy"]
   missing = [f for f in required if f not in extracted_fields]
   if missing:
       flag_specimen(specimen_id, "MISSING_REQUIRED_FIELDS",
                     f"Missing: {', '.join(missing)}")
   ```

## Implementation Components

### 1. Specimen Index (`specimen_index.db`)

SQLite database tracking specimens:

```sql
CREATE TABLE specimens (
    specimen_id TEXT PRIMARY KEY,
    camera_filename TEXT UNIQUE,
    expected_catalog_number TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE original_files (
    sha256 TEXT PRIMARY KEY,
    specimen_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    format TEXT,
    dimensions_json TEXT,
    size_bytes INTEGER,
    role TEXT, -- 'original_photo', 'original_raw'
    captured_at TIMESTAMP,
    FOREIGN KEY (specimen_id) REFERENCES specimens(specimen_id)
);

CREATE TABLE image_transformations (
    sha256 TEXT PRIMARY KEY,
    specimen_id TEXT NOT NULL,
    derived_from TEXT NOT NULL,
    operation TEXT,
    params_json TEXT,
    timestamp TIMESTAMP,
    tool TEXT,
    tool_version TEXT,
    stored_at TEXT,
    FOREIGN KEY (specimen_id) REFERENCES specimens(specimen_id),
    FOREIGN KEY (derived_from) REFERENCES original_files(sha256)
);

CREATE TABLE extractions (
    extraction_id TEXT PRIMARY KEY,
    specimen_id TEXT NOT NULL,
    image_sha256 TEXT NOT NULL,
    params_hash TEXT NOT NULL,
    run_id TEXT,
    status TEXT,
    dwc_fields_json TEXT,
    raw_jsonl_offset INTEGER,
    timestamp TIMESTAMP,
    UNIQUE(image_sha256, params_hash),
    FOREIGN KEY (specimen_id) REFERENCES specimens(specimen_id)
);

CREATE TABLE specimen_aggregations (
    specimen_id TEXT PRIMARY KEY,
    candidate_fields_json TEXT,
    best_candidates_json TEXT,
    review_status TEXT,
    queued_for_review_at TIMESTAMP,
    FOREIGN KEY (specimen_id) REFERENCES specimens(specimen_id)
);

CREATE TABLE reviews (
    specimen_id TEXT PRIMARY KEY,
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,
    decisions_json TEXT,
    final_dwc_json TEXT,
    status TEXT,
    FOREIGN KEY (specimen_id) REFERENCES specimens(specimen_id)
);

CREATE TABLE data_quality_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    specimen_id TEXT NOT NULL,
    flag_type TEXT NOT NULL,
    severity TEXT, -- 'error', 'warning', 'info'
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (specimen_id) REFERENCES specimens(specimen_id)
);

CREATE INDEX idx_catalog_numbers ON specimen_aggregations(
    json_extract(best_candidates_json, '$.catalogNumber.value')
);
```

### 2. Deduplication Service

```python
class ExtractionDeduplicator:
    """Prevents duplicate extraction of (image, params) combinations."""

    def should_extract(self, image_sha256: str, params: dict) -> tuple[bool, Optional[str]]:
        """Check if extraction should proceed.

        Returns:
            (should_extract, existing_extraction_id)
        """
        params_hash = self._hash_params(params)

        existing = db.query(
            "SELECT extraction_id, status FROM extractions "
            "WHERE image_sha256 = ? AND params_hash = ?",
            (image_sha256, params_hash)
        ).fetchone()

        if existing is None:
            return True, None

        # Re-extract if previous attempt failed
        if existing['status'] == 'failed':
            return True, existing['extraction_id']

        # Skip if already successfully extracted
        return False, existing['extraction_id']

    def _hash_params(self, params: dict) -> str:
        """Create deterministic hash of extraction parameters."""
        canonical = json.dumps(params, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()
```

### 3. Specimen Aggregator

```python
class SpecimenAggregator:
    """Aggregates multiple extraction results per specimen."""

    def aggregate_extractions(self, specimen_id: str):
        """Combine all extraction results for a specimen."""

        # Get all completed extractions for this specimen
        extractions = db.query(
            "SELECT extraction_id, dwc_fields_json FROM extractions "
            "WHERE specimen_id = ? AND status = 'completed'",
            (specimen_id,)
        ).fetchall()

        # Group by field name, collect all candidates
        candidate_fields = defaultdict(list)

        for extraction in extractions:
            dwc_fields = json.loads(extraction['dwc_fields_json'])

            for field_name, field_data in dwc_fields.items():
                candidate_fields[field_name].append({
                    'value': field_data['value'],
                    'confidence': field_data['confidence'],
                    'source': extraction['extraction_id']
                })

        # Select best candidate per field (highest confidence)
        best_candidates = {}
        for field_name, candidates in candidate_fields.items():
            best = max(candidates, key=lambda c: c['confidence'])
            best_candidates[field_name] = best

        # Save aggregation
        db.execute(
            "INSERT OR REPLACE INTO specimen_aggregations "
            "(specimen_id, candidate_fields_json, best_candidates_json, "
            " review_status, queued_for_review_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (specimen_id,
             json.dumps(dict(candidate_fields)),
             json.dumps(best_candidates),
             'pending',
             datetime.now(timezone.utc).isoformat())
        )

        return best_candidates
```

### 4. Data Quality Checker

```python
class DataQualityChecker:
    """Detects and flags invariant violations."""

    def check_catalog_number_uniqueness(self):
        """Flag specimens with duplicate catalog numbers."""

        # Find catalog numbers appearing on multiple specimens
        duplicates = db.query("""
            SELECT
                json_extract(best_candidates_json, '$.catalogNumber.value') as cat_num,
                GROUP_CONCAT(specimen_id) as specimens
            FROM specimen_aggregations
            WHERE cat_num IS NOT NULL
            GROUP BY cat_num
            HAVING COUNT(*) > 1
        """).fetchall()

        for dup in duplicates:
            cat_num = dup['cat_num']
            specimens = dup['specimens'].split(',')

            for specimen_id in specimens:
                self.flag_specimen(
                    specimen_id,
                    'DUPLICATE_CATALOG_NUMBER',
                    f"Catalog {cat_num} appears on specimens: {specimens}",
                    severity='error'
                )

    def flag_specimen(self, specimen_id: str, flag_type: str,
                     message: str, severity: str = 'warning'):
        """Add a data quality flag."""
        db.execute(
            "INSERT INTO data_quality_flags "
            "(specimen_id, flag_type, severity, message) "
            "VALUES (?, ?, ?, ?)",
            (specimen_id, flag_type, severity, message)
        )
```

## Integration with Existing System

### Migration Path

1. **Create specimen index** from existing `raw.jsonl` files:
   ```python
   # scripts/migrate_to_specimen_index.py
   # - Parse camera filenames from image hashes
   # - Create specimen records
   # - Link extraction results to specimens
   # - Detect and flag duplicates
   ```

2. **Update extraction pipeline** to use deduplication:
   ```python
   # In cli.py extract command:
   dedup = ExtractionDeduplicator(db)

   for image in images:
       should_extract, existing_id = dedup.should_extract(
           image.sha256,
           extraction_params
       )

       if not should_extract:
           logger.info(f"Skipping {image.sha256}: already extracted ({existing_id})")
           continue

       # Proceed with extraction...
   ```

3. **Add aggregation step** before review:
   ```python
   # After extraction completes:
   aggregator = SpecimenAggregator(db)

   for specimen_id in processed_specimens:
       aggregator.aggregate_extractions(specimen_id)

   # Run quality checks
   qc = DataQualityChecker(db)
   qc.check_catalog_number_uniqueness()
   qc.check_malformed_catalog_numbers()
   qc.check_missing_required_fields()
   ```

4. **Update review interface** to show:
   - All extraction attempts per specimen
   - Candidate values from multiple runs
   - Data quality flags
   - Full provenance chain

## Benefits

1. **Full Provenance**: Trace any DwC record back to original camera files
2. **Efficient Processing**: Never re-run identical (image, params) combinations
3. **Better Extraction**: Multiple attempts with different methods aggregate
4. **Data Quality**: Automatic detection of catalog number issues
5. **Audit Trail**: Complete history of what was processed, when, and by whom
6. **Reproducibility**: Exact extraction parameters recorded for every result

## Example Workflow

```python
# 1. Upload/register original files
specimen_index.register_specimen(
    specimen_id="DSC_0001",
    original_files=[
        {"path": "DSC_0001.JPG", "sha256": "abc123..."},
        {"path": "DSC_0001.NEF", "sha256": "def456..."}
    ]
)

# 2. Create transformation for OCR
transform_id = specimen_index.register_transformation(
    specimen_id="DSC_0001",
    derived_from="abc123...",
    operation="resize_for_ocr",
    sha256="000e426d..."
)

# 3. Extract (with automatic dedup check)
extraction_params = {
    "ocr_engine": "vision",
    "model": "gpt-4o-mini",
    "prompt_version": "v2.1"
}

should_extract, existing_id = dedup.should_extract("000e426d...", extraction_params)

if should_extract:
    results = run_extraction("000e426d...", extraction_params)
    specimen_index.record_extraction(
        specimen_id="DSC_0001",
        image_sha256="000e426d...",
        params=extraction_params,
        results=results
    )

# 4. Aggregate for review
best_candidates = aggregator.aggregate_extractions("DSC_0001")

# 5. Check quality
qc.check_all("DSC_0001")

# 6. Queue for human review
review_queue.add("DSC_0001")
```
