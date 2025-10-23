# Next Session Plan: v2.1.0 GBIF Validation Integration Prep

**Created**: 2025-10-23
**Session Focus**: Prepare for v2.1.0 GBIF validation integration milestone
**Timeline**: November 1-28, 2025 (4-week milestone)

---

## Current State

### ✅ Completed Today (2025-10-23)
1. Merged feature/quart-migration into main (async web app + Docker)
2. Cleaned up duplicate documentation (8 archived status docs)
3. Fixed broken documentation links (4 fixes in docs/README.md)
4. Improved bootstrap.sh UX (interactive, educational setup)
5. Created missing documentation:
   - docs/ocr_engines.md (comprehensive OCR engine guide)
   - docs/quickstart_examples.md (copy-paste ready examples)
   - docs/testing.md (complete testing guide)

### ✅ v2.0.0 Released
- Specimen-centric provenance architecture designed and documented
- Repository optimized (8.4MB, 97% reduction)
- Docker containerization complete
- Async web app (Quart) deployed
- Full backup and rollback capability in place

### 📋 Next Milestone: v2.1.0
**Goal**: Integrate GBIF validation into specimen provenance system

**Key Features**:
- Two-tier validation (automatic pre-validation + interactive review)
- Taxonomy verification via GBIF Backbone API
- Locality verification (coordinate validation)
- Quality flags for GBIF-specific issues
- Review UI enhancements for GBIF status display

---

## v2.1.0 Implementation Roadmap

### Week 1: Database Schema & Pre-Validation (Nov 1-7)

#### Tasks
- [ ] **Implement SpecimenIndex class** (`src/provenance/specimen_index.py`)
  - Specimen registration with content-addressed IDs (SHA256)
  - Extraction run tracking with parameters
  - Aggregation logic for multi-extraction results
  - Database initialization and migration

- [ ] **Add GBIF validation to database schema**
  - Add `gbif_validation_json` column to `specimen_aggregations` table
  - Create index on auto-validation status
  - Define GBIF quality flag types in `data_quality_flags` table

- [ ] **Implement automatic GBIF pre-validation**
  - Create `_auto_validate_gbif()` method in SpecimenIndex
  - Integrate with existing `qc/gbif.py` GbifLookup class
  - Auto-validate during specimen aggregation (non-blocking)
  - Generate quality flags for validation issues

- [ ] **Write integration tests**
  - Test specimen registration and deduplication
  - Test extraction run tracking
  - Test aggregation with GBIF validation
  - Test quality flag generation

#### Success Criteria
- SpecimenIndex can register specimens and track extractions
- GBIF validation runs automatically during aggregation
- Low-confidence extractions are flagged for review
- All tests pass

---

### Week 2: Review UI Integration (Nov 8-14)

#### Tasks
- [ ] **Add GBIF validation panel to review UI**
  - Display auto-validation status (badge: success/warning)
  - Show taxonomy validation results (match type, confidence)
  - Show locality validation results (coordinate validity, distance)
  - Display validation issues as actionable items

- [ ] **Implement GBIF autocomplete endpoint** (`/api/gbif/suggest`)
  - Real-time scientific name suggestions as reviewer types
  - Cache suggestions for performance
  - Handle rate limiting gracefully

- [ ] **Implement manual validation endpoint** (`/api/specimen/<id>/gbif/validate`)
  - Full GBIF validation on demand (POST request)
  - Store validation results in specimen index
  - Return updated validation status to UI

- [ ] **Add GBIF status to specimen list view**
  - Filter specimens by validation status
  - Sort by GBIF confidence
  - Quick actions (approve validated, review unvalidated)

#### Success Criteria
- Review UI shows GBIF validation status for all specimens
- Autocomplete provides relevant scientific name suggestions
- Manual validation updates specimen index correctly
- Reviewers can filter and sort by GBIF status

---

### Week 3: Testing & Refinement (Nov 15-21)

#### Tasks
- [ ] **Test pre-validation accuracy on sample data**
  - Run on subset of 2,885 specimens (e.g., 100 specimens)
  - Measure auto-validation rate (target: ~60%)
  - Verify quality flags are appropriate
  - Tune confidence thresholds if needed

- [ ] **Performance testing**
  - Measure aggregation speed with GBIF validation
  - Test autocomplete response time (target: <500ms)
  - Load test GBIF API calls (handle rate limits)
  - Optimize caching strategy

- [ ] **UI/UX refinement**
  - Collect feedback on GBIF panel design
  - Improve validation result presentation
  - Add helpful tooltips and documentation links
  - Ensure mobile responsiveness

- [ ] **Integration tests**
  - End-to-end workflow: extraction → aggregation → GBIF validation → review
  - Test error handling (API failures, rate limits)
  - Test rollback scenarios

#### Success Criteria
- Pre-validation achieves >60% auto-validation rate
- Autocomplete responds in <500ms
- GBIF API calls don't exceed rate limits
- All integration tests pass

---

### Week 4: Migration & Publication (Nov 22-28)

#### Tasks
- [ ] **Migrate existing data to v2.1.0**
  - Run `scripts/migrate_to_specimen_index.py` on 2,885 specimens
  - Verify data integrity (no data loss)
  - Generate migration report

- [ ] **Run GBIF pre-validation on all specimens**
  - Batch validate 2,885 specimens
  - Generate quality report (validation coverage, issues)
  - Create review queue (prioritize unvalidated specimens)

- [ ] **Export v2.1.0-draft publication**
  - All specimens with GBIF validation status
  - Document validation metrics
  - Create Darwin Core Archive

- [ ] **Begin human review of flagged specimens**
  - Set up review workflow for curators
  - Track review progress
  - Document common issues and resolutions

- [ ] **Release v2.1.0**
  - Tag release: `git tag v2.1.0`
  - Update CHANGELOG.md
  - Create GitHub release with notes
  - Update documentation site

#### Success Criteria
- All 2,885 specimens migrated to specimen index
- GBIF validation complete for all specimens
- v2.1.0-draft publication created
- Release tagged and documented

---

## Immediate Next Session Tasks

### 1. Review GBIF Integration Code
**Where**: `qc/gbif.py`, `src/review/validators.py`

**Questions to answer**:
- What GBIF API endpoints are currently used?
- How is caching implemented?
- What error handling exists for API failures?
- What validation metadata is returned?

**Action**: Read these files and understand current GBIF integration

---

### 2. Design SpecimenIndex Database Schema

**Required tables** (from docs/SPECIMEN_PROVENANCE_ARCHITECTURE.md):

```sql
-- Specimen registration
CREATE TABLE specimens (
    specimen_id TEXT PRIMARY KEY,  -- SHA256 of (image_sha256 + optional_identifier)
    image_sha256 TEXT NOT NULL,
    optional_identifier TEXT,
    first_seen_at TEXT NOT NULL,
    last_updated_at TEXT NOT NULL,
    metadata_json TEXT  -- Original image metadata
);

-- Extraction runs
CREATE TABLE extraction_runs (
    run_id TEXT PRIMARY KEY,  -- UUID
    specimen_id TEXT NOT NULL,
    image_sha256 TEXT NOT NULL,
    extraction_params_json TEXT NOT NULL,  -- OCR engine, config, version
    extracted_at TEXT NOT NULL,
    raw_extraction_json TEXT NOT NULL,  -- Full OCR output
    FOREIGN KEY (specimen_id) REFERENCES specimens(specimen_id)
);

-- Aggregated results (with GBIF validation)
CREATE TABLE specimen_aggregations (
    specimen_id TEXT PRIMARY KEY,
    candidate_fields_json TEXT NOT NULL,  -- All candidate values per field
    best_candidates_json TEXT NOT NULL,   -- Confidence-weighted best values
    gbif_validation_json TEXT,            -- NEW: GBIF validation results
    review_status TEXT DEFAULT 'pending', -- pending|approved|rejected
    reviewed_by TEXT,
    reviewed_at TEXT,
    queued_for_review_at TEXT,
    FOREIGN KEY (specimen_id) REFERENCES specimens(specimen_id)
);

-- Quality flags (including GBIF flags)
CREATE TABLE data_quality_flags (
    flag_id TEXT PRIMARY KEY,
    specimen_id TEXT NOT NULL,
    flag_type TEXT NOT NULL,  -- GBIF_TAXONOMY_UNVERIFIED, GBIF_INVALID_COORDINATES, etc.
    severity TEXT NOT NULL,   -- error|warning|info
    message TEXT,
    flagged_at TEXT NOT NULL,
    resolved_at TEXT,
    FOREIGN KEY (specimen_id) REFERENCES specimens(specimen_id)
);
```

**Action**: Create `src/provenance/schema.sql` with full schema definition

---

### 3. Prototype SpecimenIndex Class

**File**: `src/provenance/specimen_index.py`

**Key methods**:
- `register_specimen(image_sha256, optional_id) -> specimen_id`
- `add_extraction_run(specimen_id, params, results) -> run_id`
- `aggregate_specimen_extractions(specimen_id) -> aggregated_results`
- `_auto_validate_gbif(candidates) -> validation_results`
- `update_gbif_validation(specimen_id, validation) -> None`
- `get_specimen_for_review(specimen_id) -> dict`

**Action**: Create minimal prototype of SpecimenIndex class with database operations

---

### 4. Write Migration Script

**File**: `scripts/migrate_to_specimen_index.py`

**Purpose**: Migrate existing `raw.jsonl` data (v1.x format) to v2.1.0 specimen index

**Steps**:
1. Read `full_dataset_processing/run_20250930_181456/raw.jsonl`
2. For each extraction result:
   - Register specimen (if not already registered)
   - Add extraction run
   - Store raw extraction data
3. Aggregate extractions per specimen
4. Run GBIF pre-validation
5. Generate migration report

**Action**: Create migration script skeleton with safe rollback mechanism

---

### 5. Set Up Testing Infrastructure

**Files to create**:
- `tests/unit/test_specimen_index.py` - Unit tests for SpecimenIndex
- `tests/integration/test_gbif_validation.py` - Integration tests for GBIF validation
- `tests/integration/test_migration.py` - Migration script tests

**Action**: Create test files with basic structure and fixtures

---

## Technical Notes

### GBIF API Rate Limits
- 300 requests per minute
- Use caching aggressively (LRU cache already in `qc/gbif.py`)
- Batch operations where possible
- Implement exponential backoff on rate limit errors

### Database Performance
- Index on `specimen_id` in all tables
- Index on `gbif_validation_json` for filtering
- Consider partial indexes for common queries:
  - `WHERE review_status = 'pending'`
  - `WHERE json_extract(gbif_validation_json, '$.auto_validated') = true`

### Error Handling
- GBIF API failures should not block processing
- Store validation attempts even if failed
- Retry with exponential backoff
- Log all validation errors for debugging

---

## Success Metrics

### By End of November 2025
- [ ] 2,885 specimens migrated to specimen index
- [ ] >60% auto-validated by GBIF
- [ ] Review UI shows GBIF validation status
- [ ] v2.1.0-draft publication created
- [ ] v2.1.0 released and documented

### Quality Goals
- Zero data loss during migration
- <100ms specimen load time in review UI
- <500ms GBIF autocomplete response
- >85% GBIF validation coverage (auto + manual)

---

## Reference Documents

1. **[docs/GBIF_VALIDATION_INTEGRATION.md](docs/GBIF_VALIDATION_INTEGRATION.md)** - Complete v2.1.0 roadmap
2. **[docs/specimen_provenance_architecture.md](docs/specimen_provenance_architecture.md)** - Database design
3. **[docs/status/2025-10-22-v2.0.0-release.md](docs/status/2025-10-22-v2.0.0-release.md)** - Current state summary
4. **[docs/RELEASE_2_0_PLAN.md](docs/RELEASE_2_0_PLAN.md)** - v2.0.0 → v2.1.0 migration strategy
5. **[qc/gbif.py](qc/gbif.py)** - Existing GBIF integration code
6. **[src/review/validators.py](src/review/validators.py)** - Validation utilities

---

## Notes for Next Session

- Start with reading existing GBIF code to understand current integration
- Focus on database schema design before implementation
- Keep migration script safe (non-destructive, with rollback)
- Test on small subset (10-20 specimens) before full migration
- Document all design decisions and trade-offs

---

**Ready to begin v2.1.0 GBIF validation integration! 🚀**
