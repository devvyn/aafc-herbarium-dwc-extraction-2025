# Release 2.0.0 Plan - Specimen Provenance Architecture

## Executive Summary

Version 2.0.0 introduces **specimen-centric provenance tracking**, a fundamental architectural improvement that:
- Preserves specimen identity through image transformations
- Enables deterministic deduplication at (image, extraction_params) level
- Aggregates multiple extraction attempts per specimen
- Provides full audit trail from camera files to published Darwin Core records
- Automatically detects data quality violations

**Status**: Ready for release
**Target Date**: 2025-10-22
**Migration Impact**: Non-breaking (backward compatible with opt-in migration)

## Version Decision: 2.0.0

**Why 2.0.0 (not 1.2.0)?**
- Fundamental architectural change (image-centric → specimen-centric)
- New database schema (specimen_index.db)
- Changed extraction workflow semantics
- Sets foundation for production-scale operations

**Backward Compatibility**:
- ✅ Existing extraction runs remain valid
- ✅ Old workflow continues to work without migration
- ✅ New features opt-in via migration script
- ✅ No breaking changes to CLI interface

## Release Checklist

### 1. Pre-Release Validation

- [x] Specimen provenance architecture implemented
- [x] Migration script tested on real data
- [x] Documentation complete
- [x] Monitor TUI fixes committed
- [x] Quart migration complete
- [x] Docker support added
- [ ] Run full test suite
- [ ] Verify all examples work
- [ ] Check documentation links
- [ ] Review security considerations

### 2. Version Updates

- [ ] Bump version: `1.1.1` → `2.0.0` in `pyproject.toml`
- [ ] Update version links in CHANGELOG.md
- [ ] Update README.md with v2.0 features
- [ ] Create migration guide

### 3. Release Artifacts

- [ ] Update CHANGELOG.md with v2.0.0 entry
- [ ] Create GitHub release with notes
- [ ] Tag release: `git tag v2.0.0`
- [ ] Build and test package: `uv build`
- [ ] Create published data bundle

### 4. Documentation

- [ ] Update README with migration instructions
- [ ] Create v2.0 announcement
- [ ] Update quickstart guide
- [ ] Document breaking changes (if any)

## Migration Strategy: Three-Phase Approach

### Phase 1: Preserve History (Immediate)

**Goal**: Ensure zero data loss during transition

**Actions**:
1. **Archive current state**:
   ```bash
   # Create timestamped backup
   mkdir -p archives/pre_v2_migration_$(date +%Y%m%d)

   # Archive all extraction runs
   cp -r full_dataset_processing/* archives/pre_v2_migration_$(date +%Y%m%d)/

   # Archive published data
   cp -r full_dataset_processing/published archives/pre_v2_migration_$(date +%Y%m%d)/
   ```

2. **Create migration manifest**:
   ```json
   {
     "migration_date": "2025-10-22T...",
     "pre_migration_version": "1.1.1",
     "post_migration_version": "2.0.0",
     "extraction_runs_preserved": [...],
     "published_versions_preserved": [...],
     "specimen_index_created": "specimen_index.db",
     "migration_script": "scripts/migrate_to_specimen_index.py"
   }
   ```

3. **Validate preservation**:
   ```bash
   # Verify all files copied
   diff -r full_dataset_processing archives/pre_v2_migration_*/

   # Document checksums
   find full_dataset_processing -type f -name "*.jsonl" -exec sha256sum {} \; > migration_checksums.txt
   ```

### Phase 2: Populate Specimen Index (Safe Migration)

**Goal**: Build specimen index without modifying original data

**Actions**:
1. **Initialize specimen index**:
   ```bash
   # Create empty specimen index
   uv run python -c "from src.provenance.specimen_index import SpecimenIndex; SpecimenIndex('specimen_index.db')"
   ```

2. **Migrate extraction runs**:
   ```bash
   # Migrate all historical runs
   for run_dir in full_dataset_processing/*/; do
     if [ -f "$run_dir/raw.jsonl" ]; then
       echo "Migrating: $run_dir"
       uv run python scripts/migrate_to_specimen_index.py \
         --run-dir "$run_dir" \
         --index specimen_index.db \
         --analyze-duplicates \
         --check-quality
     fi
   done
   ```

3. **Generate migration report**:
   ```bash
   # Create comprehensive report
   uv run python scripts/migrate_to_specimen_index.py \
     --run-dir full_dataset_processing/*/ \
     --index specimen_index.db \
     --analyze-duplicates \
     --check-quality \
     > migration_report_$(date +%Y%m%d).txt
   ```

**Validation**:
- [ ] All specimens from historical runs present in index
- [ ] Duplicate extractions correctly identified
- [ ] Data quality flags generated for known issues
- [ ] No data loss (original raw.jsonl files unchanged)

### Phase 3: Progressive Publication (Incremental Updates)

**Goal**: Publish data incrementally with human review tracking

**Workflow**:

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: Progressive Publication Workflow                  │
└─────────────────────────────────────────────────────────────┘

1. Extract & Aggregate
   ↓
   [Extraction Run] → raw.jsonl → [Specimen Index]
                                          ↓
                                  [Aggregation] → best_candidates per specimen
                                          ↓
                                  [Quality Check] → flag violations

2. Publish Draft (No Human Review)
   ↓
   [Export DwC-A] → full_dataset_processing/published/v2.0.0-draft/
                    - occurrence.csv (all specimens, best candidates)
                    - meta.xml (DwC-A metadata)
                    - manifest.json (provenance)
                    - quality_flags.csv (known issues)
                    - README.md ("DRAFT - Pending Human Review")

3. Human Review (Progressive)
   ↓
   [Review Queue] → specimens sorted by priority
                    - High: Quality flags (duplicates, malformed)
                    - Medium: Low confidence extractions
                    - Low: High confidence extractions

   [Review UI] → shows:
                 - All extraction attempts per specimen
                 - Best candidate fields
                 - Quality flags
                 - Provenance chain

   [Decisions] → approve | reject | correct | flag
                 ↓
   [Specimen Index] → reviews table updated
                      ↓
                      status: approved | rejected | pending

4. Progressive Re-publication
   ↓
   [Export v2.0.0-reviewed-batch1] → Only approved specimens
   [Export v2.0.0-reviewed-batch2] → First 100 approved
   [Export v2.0.0-reviewed-batch3] → First 500 approved
   ...
   [Export v2.0.0] → Final: All approved specimens

5. Publication Metadata
   ↓
   Each export includes:
   - review_status.json (approved/pending/rejected counts)
   - reviewed_by.txt (human reviewers list)
   - review_date_range.txt (when reviews occurred)
   - quality_report.md (summary of issues found/resolved)
```

## Publication Versioning Strategy

### Draft Releases (Pre-Review)

```
full_dataset_processing/published/
├── v2.0.0-draft/              # Initial extraction, no review
│   ├── occurrence.csv          # All specimens, best candidates
│   ├── meta.xml
│   ├── manifest.json
│   ├── quality_flags.csv       # Known issues to review
│   └── README.md               # "DRAFT - PENDING HUMAN REVIEW"
```

**Metadata**:
```json
{
  "version": "2.0.0-draft",
  "status": "pending_review",
  "specimens": 2885,
  "reviewed": 0,
  "approved": 0,
  "flagged": 157,
  "quality_flags": {
    "DUPLICATE_CATALOG_NUMBER": 12,
    "MALFORMED_CATALOG_NUMBER": 45,
    "MISSING_REQUIRED_FIELDS": 100
  },
  "note": "Draft data for human review. Not suitable for publication."
}
```

### Reviewed Batches (Progressive Publication)

```
full_dataset_processing/published/
├── v2.0.0-reviewed-batch1/     # First 100 specimens reviewed
├── v2.0.0-reviewed-batch2/     # First 500 specimens reviewed
├── v2.0.0-reviewed-batch3/     # First 1000 specimens reviewed
└── v2.0.0/                     # FINAL: All approved specimens
    ├── occurrence.csv           # Only approved specimens
    ├── meta.xml
    ├── manifest.json
    ├── review_summary.json
    └── README.md                # "Publication-ready data"
```

**Review Summary**:
```json
{
  "version": "2.0.0",
  "status": "publication_ready",
  "specimens": 2723,
  "reviewed": 2885,
  "approved": 2723,
  "rejected": 162,
  "flagged_and_resolved": 157,
  "review_period": "2025-10-22 to 2025-11-15",
  "reviewers": ["devvyn@example.com", "curator@aafc.ca"],
  "quality_checks_passed": true
}
```

## Review UI Integration

### Required Updates to Review System

**1. Show Specimen-Level Data** (`src/review/web_app.py`):

```python
@app.route("/api/specimen/<specimen_id>")
async def get_specimen(specimen_id: str):
    """Get all extraction attempts and aggregated data for a specimen."""

    # Get from specimen index
    aggregation = specimen_index.get_aggregation(specimen_id)
    flags = specimen_index.get_specimen_flags(specimen_id)
    extractions = specimen_index.get_extractions(specimen_id)

    return {
        "specimen_id": specimen_id,
        "candidate_fields": aggregation["candidate_fields"],
        "best_candidates": aggregation["best_candidates"],
        "quality_flags": flags,
        "extraction_history": extractions,
        "review_status": "pending"
    }
```

**2. Review Decision Tracking**:

```python
@app.route("/api/specimen/<specimen_id>/review", methods=["POST"])
async def submit_review(specimen_id: str):
    """Submit human review decision."""
    data = await request.get_json()

    # Record review in specimen index
    specimen_index.record_review(
        specimen_id=specimen_id,
        reviewed_by=data["reviewer_email"],
        decisions=data["field_decisions"],
        final_dwc=data["approved_values"],
        status=data["status"]  # approved | rejected | flagged
    )

    # Re-aggregate if corrections made
    if data["status"] == "approved":
        specimen_index.aggregate_specimen_extractions(specimen_id)

    return {"success": True}
```

**3. Review Queue Priority**:

```python
def get_review_queue(priority: str = "high"):
    """Get specimens prioritized for review."""

    if priority == "high":
        # Specimens with quality flags
        return specimen_index.get_flagged_specimens()

    elif priority == "medium":
        # Low confidence extractions
        return specimen_index.get_low_confidence_specimens(threshold=0.7)

    elif priority == "low":
        # High confidence, no flags
        return specimen_index.get_high_confidence_specimens(threshold=0.9)

    else:
        # All pending
        return specimen_index.get_pending_specimens()
```

## Data Safety Guarantees

### 1. Original Data Immutability

- ✅ Never modify original `raw.jsonl` files
- ✅ Specimen index is additive only (new database)
- ✅ Reviews stored separately from extractions
- ✅ All historical data preserved in archives

### 2. Rollback Capability

```bash
# Rollback to pre-v2.0 state
rm specimen_index.db
git checkout v1.1.1
# All extraction runs still valid, no data lost
```

### 3. Validation Checks

```bash
# Before publishing, verify:
uv run python scripts/validate_publication.py \
    --specimen-index specimen_index.db \
    --published-dir full_dataset_processing/published/v2.0.0 \
    --check-completeness \
    --check-quality \
    --check-provenance
```

### 4. Audit Trail

Every action tracked:
- Extraction: `specimen_index.extractions` table (when, what params, result)
- Aggregation: `specimen_index.specimen_aggregations` table (when, best candidates)
- Review: `specimen_index.reviews` table (who, when, what changed)
- Publication: `manifest.json` in each published version (what was included)

## Timeline

### Week 1: Release & Initial Migration (Oct 22-28)
- [x] Day 1: Create v2.0.0 release
- [ ] Day 2: Migrate all historical runs to specimen index
- [ ] Day 3: Generate migration report and validate
- [ ] Day 4: Publish v2.0.0-draft (no human review)
- [ ] Day 5-7: Documentation and announcement

### Week 2-4: Human Review (Oct 29 - Nov 18)
- Update review UI with specimen-level view
- Review high-priority specimens (flagged)
- Review medium-priority (low confidence)
- Progressive publication of reviewed batches

### Week 5: Final Publication (Nov 19-25)
- Complete remaining reviews
- Quality validation
- Publish v2.0.0 final
- Submit to GBIF/Canadensys

## Success Criteria

### Technical
- [x] Specimen index created and populated
- [ ] Zero data loss (all checksums match)
- [ ] Deduplication working (prevents redundant extractions)
- [ ] Quality flags generated for known issues
- [ ] Review UI shows specimen-level aggregation

### Scientific
- [ ] Human review tracking operational
- [ ] Progressive publication workflow validated
- [ ] Quality improvements documented
- [ ] Full provenance chain verified

### Operational
- [ ] Migration completed in < 1 hour
- [ ] Documentation complete
- [ ] Team trained on new workflow
- [ ] Rollback plan tested

## Next Steps

1. **Immediate** (Today):
   - Update version to 2.0.0
   - Update CHANGELOG
   - Create GitHub release

2. **This Week**:
   - Run migration on all historical data
   - Publish v2.0.0-draft
   - Update review UI

3. **Next 3 Weeks**:
   - Human review workflow
   - Progressive publication
   - Final v2.0.0 release

## Questions & Decisions

### Open Questions

1. **Catalog Number Pattern**: What's the official AAFC pattern for validation?
   - Currently: `^AAFC-\d{5,6}$`
   - Adjust in `specimen_index.check_malformed_catalog_numbers()`

2. **Review Priority**: Should we review flagged specimens first or random sample?
   - Recommendation: Flagged → Low confidence → High confidence

3. **Publication Frequency**: How often to publish reviewed batches?
   - Recommendation: Weekly until complete

### Decisions Made

- ✅ Version 2.0.0 (not 1.2.0) due to architectural significance
- ✅ Backward compatible migration (opt-in)
- ✅ Progressive publication (draft → batches → final)
- ✅ Specimen-centric data model

## Related Documentation

- **Architecture**: `docs/specimen_provenance_architecture.md`
- **Implementation**: `src/provenance/specimen_index.py`
- **Migration**: `scripts/migrate_to_specimen_index.py`
- **Analysis**: `docs/extraction_run_analysis_20250930.md`
