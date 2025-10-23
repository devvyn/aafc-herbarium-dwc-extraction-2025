# Feature Planning & Roadmap Alignment

**Last Updated**: 2025-10-23
**Project Phase**: Production deployment (2 months remaining handover window)
**Test Coverage**: 270/270 passing (100% success rate)
**v2.0.0 Architecture**: Provenance tracking operational

## Executive Summary

The herbarium digitization toolkit is production-ready with 95% OCR accuracy. This document prioritizes features aligned with stakeholder needs and handover requirements.

### Current Status
- ✅ 2,800 specimen photos captured
- ✅ Apple Vision OCR validated (95% accuracy vs 15% Tesseract)
- ✅ v2.0.0 provenance architecture complete
- ✅ Comprehensive test suite (270 tests passing)
- ⏳ Production deployment in progress
- ⏳ Handover preparation (8-week timeline)

## Priority Framework

Features categorized by:
1. **P0**: Critical for handover (Weeks 1-2)
2. **P1**: Important for successor productivity (Weeks 3-4)
3. **P2**: Nice-to-have enhancements (Weeks 5-8)
4. **Future**: Post-handover institutional growth

---

## P0: Critical for Production Deployment (Weeks 1-2)

### 1. Bulk Processing Pipeline Optimization
**Status**: Partially complete
**Effort**: 2-3 days
**Impact**: Essential for processing 2,800 specimens

**Current gaps**:
- [ ] Batch processing mode for 2.8k images (see `agents/pipeline_composer.py:229`)
- [ ] Progress monitoring for large batches (see `scripts/monitor_extraction_progress.py:174`)
- [ ] Resume capability for interrupted runs
- [ ] Memory optimization for sustained processing

**Implementation**:
```python
# agents/pipeline_composer.py - Add batch flag
pipeline_config = {
    "steps": ["image_to_dwc"],
    "batch_mode": True,  # Process in chunks
    "batch_size": 100,   # Optimize for memory
}
```

**Success metrics**:
- Process 2,800 images in <8 hours
- <2GB memory usage sustained
- Auto-resume on failures

### 2. Quality Control Confidence Thresholds
**Status**: Missing
**Effort**: 1-2 days
**Impact**: Reduces manual review workload

**Current gaps**:
- [ ] Confidence-based flagging (see `agents/pipeline_composer.py:246-247`)
- [ ] Selective field extraction (16 high-value fields vs all fields)
- [ ] Low-confidence specimen routing

**Implementation**:
```python
# Add confidence validation step
if confidence < 0.85:
    flag_for_review(specimen, reason="low_confidence")
    suggest_gpt_extraction(specimen)  # Fallback to GPT for difficult cases
```

**Success metrics**:
- <20% specimens flagged for review
- Clear confidence scores per field
- Automated high-confidence approval

### 3. Export to SharePoint Integration
**Status**: Missing

**Effort**: 3-4 days
**Impact**: Critical for institutional workflow

**Current gaps**:
- [ ] SharePoint upload script
- [ ] Spreadsheet template generation
- [ ] Network authentication handling
- [ ] Batch export scheduling

**Implementation**:
```bash
# New script: scripts/export_to_sharepoint.py
python scripts/export_to_sharepoint.py \
    --input processed_output/ \
    --sharepoint-site "AAFC-SRDC" \
    --folder "Herbarium Digitization 2025" \
    --format excel
```

**Success metrics**:
- One-click export to SharePoint
- Standardized spreadsheet template
- Works on institutional network

---

## P1: Successor Productivity (Weeks 3-4)

### 4. Web Review Interface Polish
**Status**: Functional but needs UX improvements
**Effort**: 2-3 days
**Impact**: Speeds up manual review by 3-5x

**Current gaps**:
- [ ] Keyboard shortcuts for common corrections
- [ ] Batch approval workflow
- [ ] Common value autocomplete (collectors, locations)
- [ ] Side-by-side image comparison

**See**: `review_web.py` - existing web interface

### 5. Photography Best Practices Documentation
**Status**: Missing
**Effort**: 1 day
**Impact**: Ensures consistent image quality

**Deliverables**:
- [ ] Camera setup guide with optimal settings
- [ ] Lighting box positioning diagrams
- [ ] Common issues and troubleshooting
- [ ] Example good/bad photos

**Location**: `docs/guides/PHOTOGRAPHY_GUIDE.md`

### 6. Lineage Tracking for Resized Images
**Status**: Partially implemented (v2.0.0)
**Effort**: 1-2 days
**Impact**: Complete audit trail

**Current gaps** (see `scripts/fetch_and_process.py:61-119`):
- [ ] Link resized SHA256 hashes to original filenames
- [ ] Track transformation parameters
- [ ] Integrate with specimen_index provenance

**Implementation**:
```python
# Use v2.0.0 provenance system
from src.provenance.specimen_index import ImageTransformation

transformation = ImageTransformation(
    sha256=resized_sha256,
    specimen_id=specimen_id,
    derived_from=original_sha256,
    operation="resize_for_processing",
    params={"max_dim": 4000, "format": "jpg"},
    tool="PIL",
    tool_version="10.0.0",
)
index.register_transformation(transformation)
```

---

## P2: Enhancement & Polish (Weeks 5-8)

### 7. Import Bundle Review Function
**Status**: Stub implementation
**Effort**: 2 days
**Impact**: Validates exports before handoff

**Current state** (see `tests/unit/test_import_review.py:15`):
```python
# TODO: Implement import_bundle() function in import_review module
```

**Implementation**:
- [ ] Load Darwin Core archive
- [ ] Validate against schema
- [ ] Generate quality report
- [ ] Flag inconsistencies

### 8. GPT Prompt Evaluation Harness
**Status**: Missing
**Effort**: 3 days
**Impact**: Improves extraction accuracy

**GitHub Issue**: [#195](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/195)

**Features**:
- [ ] Template coverage testing
- [ ] A/B prompt comparison
- [ ] Accuracy metrics by field
- [ ] Cost tracking

### 9. TUI Export Functionality
**Status**: Stub
**Effort**: 1 day
**Impact**: Alternative to web interface

**Current state** (see `tui_interface.py:514`):
```python
# TODO: Implement actual export
```

---

## Future Features (Post-Handover)

### Multilingual OCR Support
**GitHub Issue**: [#138](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/138)
**Priority**: Future (Canadian collections mostly English/French)
**Effort**: 1-2 weeks

**Languages**:
- French (common in Canadian historical collections)
- Latin (scientific names - already handled)
- German (historical collectors)

**Approach**:
- Test Tesseract language packs
- Evaluate Apple Vision multilingual performance
- Language detection preprocessing

### GBIF Taxonomy & Locality Verification
**GitHub Issue**: [#139](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/139)
**Priority**: High value but not critical for initial handoff
**Effort**: 1 week

**Features**:
- [ ] GBIF API integration for species validation
- [ ] Geographic name resolution (see `scripts/correct_interactive.py:107`)
- [ ] Automated flagging of taxonomic inconsistencies
- [ ] Locality search from GBIF occurrences

### GPU-Accelerated Tesseract
**GitHub Issue**: [#186](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/186)
**Priority**: Low (Apple Vision already optimal)
**Effort**: 1 week

**Rationale**: With Apple Vision at 95% accuracy, GPU Tesseract provides minimal ROI.

### Ensemble/Consensus Voting
**Status**: Planned but not needed
**Effort**: 1-2 weeks
**Impact**: Marginal accuracy improvement

**Current placeholders** (see `agents/pipeline_composer.py:279-280`):
```python
# TODO: "image_to_dwc_claude",  # Claude extraction
# TODO: "ensemble_vote",  # Consensus voting
# TODO: "dual_vote",  # Two-engine consensus
```

**Decision**: Defer unless Apple Vision accuracy drops below 90%

### Mapping Rules Population
**GitHub Issue**: [#157](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/157)
**Priority**: Nice-to-have
**Effort**: 2-3 days

**Files**:
- `config/rules/dwc_rules.toml` - Field validation rules
- `config/rules/vocab.toml` - Controlled vocabularies

**Implementation**:
- [ ] Common collector name variations
- [ ] Saskatchewan locality mappings
- [ ] Institution codes (AAFC, DAO, etc.)

### Audit Trail with User Sign-Off
**GitHub Issue**: [#193](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/193)
**Priority**: Institutional compliance
**Effort**: 1 week

**Features**:
- [ ] Cryptographic signatures on reviews
- [ ] Reviewer identity tracking
- [ ] Tamper-evident audit logs
- [ ] Compliance reporting

---

## Addressable TODOs by Priority

### High Priority (Complete in Weeks 1-2)
1. ✅ Batch processing flag (`agents/pipeline_composer.py:229`)
2. ✅ Confidence validation step (`agents/pipeline_composer.py:246-247`)
3. ✅ Incremental validation (`scripts/monitor_extraction_progress.py:174`)
4. 🔄 SharePoint export implementation (new)

### Medium Priority (Weeks 3-6)
5. 🔄 Lineage tracking for resized images (`scripts/fetch_and_process.py:61-119`)
6. 🔄 Import bundle review (`tests/unit/test_import_review.py:15`)
7. 🔄 TUI export (`tui_interface.py:514`)

### Low Priority (Weeks 7-8 or Future)
8. 📅 GBIF locality search (`scripts/correct_interactive.py:107`)
9. 📅 Selective 16-field extraction (`agents/pipeline_composer.py:252`)
10. 📅 Ensemble voting system (`agents/pipeline_composer.py:279-280`)

---

## Recommended Next Steps

### Week 1: Production Deployment Focus
1. **Implement batch processing** - Process 2.8k images
2. **Add confidence thresholds** - Auto-flag low-confidence results
3. **Create SharePoint export** - Institutional integration

### Week 2: Quality & Documentation
4. **Polish web review UX** - Keyboard shortcuts, autocomplete
5. **Write photography guide** - Camera setup best practices
6. **Test full workflow** - End-to-end with sample 100 specimens

### Weeks 3-4: Handover Preparation
7. **Complete lineage tracking** - Full audit trail
8. **Document workflows** - Step-by-step guides
9. **Train successor** - Hands-on sessions

### Weeks 5-8: Polish & Future-Proofing
10. **GBIF integration** - Taxonomy validation
11. **Mapping rules** - Common corrections
12. **Audit trail** - Compliance features

---

## Success Criteria

### Technical Excellence
- ✅ 100% test pass rate (270/270 tests)
- ✅ 95% OCR accuracy on real specimens
- ✅ Complete provenance tracking (v2.0.0)
- 🔄 <8 hour processing time for 2.8k images
- 🔄 <20% manual review rate

### Institutional Impact
- 🔄 2,800 specimens processed with quality scores
- 🔄 SharePoint-ready datasets
- 🔄 Successor trained and productive
- 🔄 Clear roadmap for remaining collections

### Sustainability
- ✅ Comprehensive documentation
- ✅ Automated testing infrastructure
- 🔄 Handover package complete
- 🔄 Long-term maintenance plan

---

## GitHub Issues to Address

### Can Close Now
- None identified (all tests passing, architecture stable)

### Should Create
1. **Batch Processing Enhancement** - Implement batch mode flag and progress monitoring
2. **SharePoint Integration** - Export workflow for institutional systems
3. **Photography Guide** - Best practices documentation
4. **Lineage Tracking Completion** - Link resized images to originals

### Can Defer
- #138 (Multilingual OCR) - Not critical for English/Latin labels
- #186 (GPU Tesseract) - Apple Vision already optimal
- Ensemble voting TODOs - Marginal benefit

---

**Next Action**: Review this plan with stakeholders and prioritize Weeks 1-2 features for immediate implementation.
