# OCR Cache Architecture

**Status**: ✅ Implemented (v0.2.0+)
**Issue**: [#220](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/220)

## Problem Statement

The original architecture duplicated OCR work across processing runs because results were tied to `run_id`. Processing the same 2,885 specimens twice meant running OCR 5,770 times instead of reusing cached results.

**Impact**:
- **Computational waste**: ~8 hours of redundant OCR on re-runs
- **Storage bloat**: Duplicate OCR results for identical images
- **Missed optimization**: No way to resume across run boundaries

## Solution: Run-Agnostic Deduplication

### Core Principle

**Separate data (OCR results) from metadata (processing runs)**

OCR results are **immutable data** derived from `(specimen_id, engine, engine_version)`. Processing runs are **metadata** describing when and how data was generated.

### Database Schema

#### New: `ocr_cache.db`

```sql
-- Global OCR results (persistent, deduplicated)
CREATE TABLE ocr_results (
    specimen_id VARCHAR NOT NULL,        -- SHA256 hash of image
    engine VARCHAR NOT NULL,             -- "vision", "tesseract", "gpt"
    engine_version VARCHAR,              -- e.g., "gpt-4-vision-20240101"
    extracted_text TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    error BOOLEAN NOT NULL,
    ocr_timestamp VARCHAR NOT NULL,
    PRIMARY KEY (specimen_id, engine, engine_version)
);

-- Processing runs (metadata only)
CREATE TABLE processing_runs (
    run_id VARCHAR PRIMARY KEY,
    started_at VARCHAR NOT NULL,
    completed_at VARCHAR,
    config_snapshot JSON NOT NULL,       -- Full config for reproducibility
    git_commit VARCHAR,
    operator VARCHAR
);

-- Run lineage (what was processed in each run)
CREATE TABLE run_lineage (
    run_id VARCHAR NOT NULL,
    specimen_id VARCHAR NOT NULL,
    processing_status VARCHAR NOT NULL,  -- "completed", "failed", "skipped", "cached"
    processed_at VARCHAR,
    cache_hit BOOLEAN NOT NULL,
    PRIMARY KEY (run_id, specimen_id)
);
```

#### Legacy: `candidates.db`

Still maintained for backward compatibility during migration:

```sql
CREATE TABLE candidates (
    run_id VARCHAR NOT NULL,
    image VARCHAR NOT NULL,
    value TEXT NOT NULL,
    engine VARCHAR NOT NULL,
    confidence FLOAT NOT NULL,
    error BOOLEAN NOT NULL,
    PRIMARY KEY (run_id, image, value, engine)
);
```

**Migration strategy**: Dual-write to both schemas. Drop `candidates` in future release.

## Implementation

### Cache Lookup Flow

```python
# cli.py - image_to_text step

# 1. Check cache first
specimen_sha = compute_sha256(img_path)
cached = get_cached_ocr(cache_session, specimen_sha, preferred_engine)

if cached and not cached.error:
    # Use cached result (cache hit)
    text = cached.extracted_text
    confidences = [cached.confidence]
    record_lineage(cache_session, run_id, specimen_sha, "cached", cache_hit=True)
else:
    # Run OCR (cache miss)
    text, confidences = dispatch("image_to_text", image=proc_path, engine=preferred, **kwargs)
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

    # Cache the result for future runs
    cache_ocr_result(cache_session, specimen_sha, preferred, text, avg_conf)
    record_lineage(cache_session, run_id, specimen_sha, "completed", cache_hit=False)
```

### Cache API

**Module**: `io_utils/ocr_cache.py`

```python
from io_utils.ocr_cache import (
    init_db,                    # Initialize ocr_cache.db
    get_cached_ocr,             # Retrieve cached OCR result
    cache_ocr_result,           # Store OCR result in cache
    record_run,                 # Record processing run metadata
    complete_run,               # Mark run as completed
    record_lineage,             # Track specimen processing in run
    get_cache_stats,            # Get cache hit statistics
)

# Initialize
cache_session = init_db(output / "ocr_cache.db")

# Check cache
cached = get_cached_ocr(session, specimen_id="abc123", engine="vision", engine_version=None)

# Cache result
cache_ocr_result(
    session,
    specimen_id="abc123",
    engine="vision",
    extracted_text="AAFC #12345...",
    confidence=0.95,
    engine_version=None,
    error=False
)

# Track run
record_run(session, run_id="run_20251005", config=cfg)
record_lineage(session, run_id, specimen_id, "cached", cache_hit=True)
complete_run(session, run_id)

# Get stats
stats = get_cache_stats(session, run_id)
# {'total': 2885, 'cache_hits': 2885, 'new_ocr': 0, 'cache_hit_rate': 1.0}
```

## Performance Results

### Test Run (10 specimens)

```bash
# Run 1: Initial processing
$ python cli.py process --input test_small/ --output test_cache/
INFO: Processed 10 images | Cache stats: 0 hits, 10 new OCR, 0.0% hit rate

# Run 2: Re-run same specimens
$ python cli.py process --input test_small/ --output test_cache/
INFO: Processed 10 images | Cache stats: 10 hits, 0 new OCR, 100.0% hit rate
```

**Result**: 100% cache hit rate on second run → Zero redundant OCR

### Production Impact

**Before caching:**
```
Run 1: 2,885 specimens → 8 hours OCR
Run 2: 2,885 specimens → 8 hours OCR again
Total: 16 hours
```

**After caching:**
```
Run 1: 2,885 specimens → 8 hours OCR
Run 2: 2,885 specimens → <1 minute (cache hits)
Total: ~8 hours
```

**Savings**: 50% reduction in processing time for repeated runs

## Use Cases

### 1. Resume Across Runs

**Before**: Resume only worked within same run
```bash
# Interrupted run - had to start over
$ python cli.py process --input images/
^C  # Ctrl-C
$ python cli.py process --input images/  # ❌ Starts OCR from scratch
```

**After**: Resume works globally
```bash
# Interrupted run - picks up from cache
$ python cli.py process --input images/
^C  # Ctrl-C
$ python cli.py process --input images/  # ✅ Uses cached OCR results
```

### 2. Engine Comparison

Test different OCR engines without re-processing:

```bash
# Run with Apple Vision
$ python cli.py process --input images/ --output run1/ --engine vision

# Try Tesseract (reuses Vision results, only runs Tesseract)
$ python cli.py process --input images/ --output run2/ --engine tesseract
# Cache: Vision results preserved, Tesseract runs fresh
```

### 3. Configuration Experiments

Change pipeline settings without repeating OCR:

```bash
$ python cli.py process --config experiment1.toml --input images/
# OCR runs, results cached

$ python cli.py process --config experiment2.toml --input images/
# OCR skipped (cache hit), only pipeline changes processed
```

### 4. Partial Reprocessing

Reprocess only low-confidence specimens:

```bash
# Future feature (not yet implemented)
$ python cli.py reprocess --filter "confidence < 0.8"
# Skips 2,660 high-confidence specimens, only processes 225 low-confidence
```

## Provenance & Lineage

The cache maintains **full audit trail** without sacrificing efficiency:

### Query Examples

**Which specimens were processed in a run?**
```sql
SELECT specimen_id, processing_status, cache_hit
FROM run_lineage
WHERE run_id = 'run_20251005_122526';
```

**What OCR engines have processed this specimen?**
```sql
SELECT engine, engine_version, extracted_text, confidence, ocr_timestamp
FROM ocr_results
WHERE specimen_id = 'abc123...';
```

**Cache hit rate across all runs?**
```sql
SELECT
    run_id,
    COUNT(*) as total,
    SUM(cache_hit) as hits,
    ROUND(100.0 * SUM(cache_hit) / COUNT(*), 1) as hit_rate_pct
FROM run_lineage
GROUP BY run_id
ORDER BY run_id;
```

**When was this specimen first OCR'd?**
```sql
SELECT MIN(ocr_timestamp) as first_ocr
FROM ocr_results
WHERE specimen_id = 'abc123...';
```

## Engine Versioning

Cache tracks engine versions to detect when reprocessing is needed:

```python
# Check if current engine version has processed this specimen
cached = get_cached_ocr(session, specimen_id, "gpt", engine_version="gpt-4o")

if not cached:
    # New engine version - run fresh OCR
    text, conf = dispatch("image_to_text", image=img, engine="gpt", model="gpt-4o")
    cache_ocr_result(session, specimen_id, "gpt", text, conf, engine_version="gpt-4o")
```

**Example**: Upgrading from `gpt-4-vision` to `gpt-4o` triggers reprocessing only for specimens that haven't been processed with the new version.

## Migration Path

### Phase 1: ✅ Dual-Write (Current)
- Write to both `candidates.db` (old) and `ocr_cache.db` (new)
- Read from cache before OCR
- Log cache stats
- **Status**: Implemented in v0.2.0

### Phase 2: Validation (Future)
- Monitor cache hit rates in production
- Verify data consistency between schemas
- Collect performance metrics

### Phase 3: Cutover (Future)
- Switch to cache-only writes
- Deprecate `candidates.db`
- Update review UI to use `ocr_cache.db`

### Phase 4: Backfill (Future)
- Import OCR results from historical runs
- Build complete lineage graph
- Generate cross-run provenance reports

## Testing

**Test Suite**: `tests/unit/test_ocr_cache.py` (11 tests)

```bash
$ uv run pytest tests/unit/test_ocr_cache.py -v
```

**Coverage**:
- ✅ Cache initialization
- ✅ OCR result roundtrip (store & retrieve)
- ✅ Deduplication (same specimen+engine)
- ✅ Engine versioning (separate cache entries)
- ✅ Cache miss handling
- ✅ Run tracking & completion
- ✅ Lineage recording
- ✅ Cache statistics calculation
- ✅ Error result caching
- ✅ Multi-engine support

## Monitoring

Cache performance is logged on every run:

```
INFO: Processed 2885 images. Output written to run_20251005/ |
      Cache stats: 2850 hits, 35 new OCR, 98.8% hit rate
```

**Metrics tracked**:
- `total`: Total specimens processed
- `cache_hits`: Specimens using cached OCR
- `new_ocr`: Specimens requiring fresh OCR
- `failed`: OCR failures
- `skipped`: Specimens skipped (resume mode)
- `cache_hit_rate`: Efficiency percentage

## Future Enhancements

1. **Global cache across projects**
   - Share OCR results between AAFC herbarium runs
   - Centralized specimen registry

2. **Selective invalidation**
   - Expire cache entries after N days
   - Force refresh for specific specimens

3. **Cache warming**
   - Pre-populate cache from S3 manifest
   - Batch OCR for new specimens

4. **Distributed caching**
   - Redis/memcached for multi-worker processing
   - Shared cache across compute nodes

## Related Architecture

- **Issue #214**: [Image Lineage Tracking](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/214)
- **Issue #218**: [Fetch Strategy](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/218)
- **Issue #219**: [Comprehensive Provenance](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/219)

## References

- **Implementation PR**: [Link when merged]
- **Test Coverage**: `tests/unit/test_ocr_cache.py`
- **Module**: `io_utils/ocr_cache.py`
- **Integration**: `cli.py:212-269` (image_to_text cache lookup)
