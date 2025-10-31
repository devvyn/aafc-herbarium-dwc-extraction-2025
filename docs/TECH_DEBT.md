# Technical Debt Inventory

**Created**: 2025-10-23
**Status**: Deferred to post-stakeholder-delivery
**Review Date**: After AAFC data handoff to Dr. Leeson (target: November 2025)

## Purpose

This document captures all TODO markers and deferred improvements identified during v2.0.0 development. These items are **intentionally deferred** - they do not block stakeholder delivery and can be addressed after the primary mission (processing 2,800 specimens for AAFC) is complete.

**Current priority**: Deliver processed data to Dr. Julia Leeson. Everything in this document is lower priority than that goal.

---

## Category 1: User Interface Enhancements

### TUI Export Functionality
**Location**: `tui_interface.py`
**Status**: Placeholder implementation
**Impact**: Low - stakeholders use web review interface and CSV exports

```python
# TODO: Implement actual export
with self.console.status("Creating archive...", spinner="dots"):
    time.sleep(2)  # Simulate export
```

**Decision**: TUI is secondary interface. Web app (Quart) is production interface. Defer until TUI becomes primary workflow.

**Estimated effort**: 4-6 hours
**Priority**: Low (P3)

### NiceGUI Review Interface Investigation
**Location**: `archive/experimental/nicegui-review-ui/`
**Status**: Archived - filter state management bug
**Impact**: Low - Quart web app is stable and production-ready

**Context**: Attempted Python-native review interface using NiceGUI framework to avoid JavaScript complexity. Implementation complete (~30KB) with zone visualization, rotation caching, and GBIF integration.

**Blocking Issue**: Filter UI disappears after dropdown interaction due to NiceGUI reactive framework state management bug. Diagnostic tool (`test_filter_bug.py`) reproduces issue with Selenium.

**Options**:
1. **Debug NiceGUI reactivity** (8-12 hours) - Understand state management, simplify filter rendering
2. **Abandon NiceGUI** (2 hours) - Remove from dependencies, delete archived code, document Quart as canonical
3. **Wait for NiceGUI updates** (0 hours) - Revisit after framework matures

**Decision Pending**: Recommend option 2 (abandon). Quart works well, and debugging NiceGUI complexity outweighs benefit of Python-native UI.

**Estimated effort**: 2-12 hours depending on option
**Priority**: Low (P3)

---

## Category 2: Pipeline Architecture (Future Research)

### Pipeline Composer Enhancements
**Location**: `agents/pipeline_composer.py`
**Status**: Multiple research-oriented TODOs
**Impact**: Medium - these are optimizations for future scale/quality

#### 2a. Batch Mode Flag
```python
steps=["image_to_dwc"],  # TODO: Add batch mode flag
```
**Context**: Enable explicit batch vs streaming processing modes
**Priority**: Medium (P2) - useful when processing >10k specimens

#### 2b. Confidence-Based Selective Processing
```python
# TODO: Add "validate_confidence" step
# TODO: Add "gpt_if_needed" for low-confidence specimens
```
**Context**: Progressive quality strategy - use free engines first, upgrade to paid only for low-confidence results
**Impact**: Cost optimization at scale
**Priority**: Medium (P2) - valuable for multi-institution deployments

#### 2c. 16-Field Selective Extraction
```python
fields_extracted=7,  # TODO: Selective 16-field extraction
```
**Context**: Current production uses 7-field baseline. 16-field extraction works but not yet default
**Priority**: Low (P3) - GBIF only requires 7 core fields

#### 2d. Ensemble Voting
```python
# TODO: "image_to_dwc_claude",  # Claude extraction
# TODO: "ensemble_vote",  # Consensus voting
# TODO: "dual_vote",  # Two-engine consensus
```
**Context**: Research-grade multi-model validation
**Impact**: Higher accuracy, significantly higher cost
**Priority**: Low (P3) - research experiment, not production requirement
**Estimated cost**: $30-50 per 1,000 specimens (vs $3.70 current)

**Decision**: Current 98% quality meets stakeholder needs. Defer ensemble research until quality requirements increase.

---

## Category 3: Data Provenance & Lineage

### S3 Kit Integration
**Location**: `scripts/fetch_and_process.py`
**Status**: External dependency management
**Impact**: Low - current approach works

```python
# TODO: Eventually move s3-image-dataset-kit into this codebase as a module
# For now, add it to path
S3_KIT_PATH = Path.home() / "Documents/GitHub/s3-image-dataset-kit/src"
```

**Decision**: External git submodule or vendoring is cleaner architecture, but current sys.path approach works for single-user deployment.

**Priority**: Low (P3)
**Trigger**: When multiple users need deployment OR when publishing toolkit

### Enhanced Lineage Tracking
**Location**: `scripts/fetch_and_process.py`
**Status**: V2.0.0 has specimen-centric provenance; these are enhancements

```python
# TODO(human): Implement fetch strategy and lineage tracking
# Lineage tracking TODO:
# - Link resized images (SHA256 hashes) back to original camera files

# Metadata:
"manifest_version": "v1",  # TODO: extract from manifest metadata
"lineage_tracking": "TODO: Link resized SHA256 hashes to original filenames",
"future_work": "See GitHub issue for comprehensive provenance system",
```

**Context**: V2.0.0 already tracks specimen lineage (image SHA256 → extractions → review). These TODOs describe linking back to original camera filenames (DSC_*.JPG → resized versions).

**Priority**: Low (P3) - nice for audit trail, not required for GBIF publication
**Trigger**: If institutional compliance requires full camera-to-publication lineage

---

## Category 4: Monitoring & Validation

### Incremental Validation
**Location**: `scripts/monitor_extraction_progress.py`
**Status**: Manual validation works; incremental would be optimization

```python
# TODO: Implement incremental validation
print("\n✅ Validation: Available (run full validation manually)")
```

**Decision**: Full validation runs are acceptable for current scale (2,800 specimens). Incremental validation valuable at >10k specimens.

**Priority**: Low (P3)

---

## Category 5: Interactive Correction Tools

### GBIF Locality Search
**Location**: `scripts/correct_interactive.py`
**Status**: Hardcoded common localities, GBIF API integration possible

```python
# TODO: Implement locality search from GBIF occurrences
# For now, return common Saskatchewan localities
common_localities = [...]
```

**Context**: Interactive correction tool for manual review. Current approach (hardcoded Saskatchewan localities) works for AAFC herbarium. GBIF API would enable auto-complete from global occurrence data.

**Priority**: Low (P3) - enhancement, not blocker
**Estimated effort**: 6-8 hours (GBIF API integration + caching)

---

## Category 6: Testing Infrastructure

### Import Bundle Test
**Location**: `tests/unit/test_import_review.py`
**Status**: Test written for unimplemented feature

```python
TODO: Implement import_bundle() function in import_review module
Expected behavior:
- Load bundle.zip containing candidates.db + manifest.json
```

**Context**: Test-driven development artifact. The `import_bundle()` function was planned but not implemented.

**Decision**: Remove test or implement feature if bundle import becomes requirement.

**Priority**: Low (P3)

---

## Summary Statistics

**Total TODOs**: 17
**Category breakdown**:
- UI enhancements: 1
- Pipeline research: 6
- Provenance tracking: 4
- Monitoring: 1
- Interactive tools: 1
- Testing: 1
- Metadata extraction: 3

**Blocking stakeholder delivery**: 0
**High priority (P1)**: 0
**Medium priority (P2)**: 3 (batch mode, confidence validation, 16-field extraction)
**Low priority (P3)**: 14

---

## Review Process

**When to revisit**:
1. ✅ After successful data handoff to Dr. Leeson
2. After GBIF publication of initial dataset
3. When scaling to >10,000 specimens
4. When multi-institution deployment is planned
5. When research-grade quality (>98%) is required

**Process**:
1. Review this document in context of new requirements
2. Promote relevant items to GitHub issues with proper prioritization
3. Update roadmap based on stakeholder feedback
4. Delete obsolete TODOs that are no longer relevant

---

## Developer Notes

**Why this document exists**:
- Captures legitimate future work without cluttering active development
- Prevents "TODO anxiety" - these are documented, not forgotten
- Enables focused delivery: stakeholder value first, optimizations later
- Provides context for future maintainers

**Philosophy**:
> "Perfect is the enemy of shipped. These TODOs represent good ideas, but shipping working software to stakeholders is better than perfecting code that already works."

**Last reviewed**: 2025-10-23
**Next review**: After AAFC data handoff (target November 2025)
