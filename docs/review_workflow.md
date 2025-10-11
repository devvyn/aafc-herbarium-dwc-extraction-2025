# Specimen Review Workflow Guide

**System**: Web-based review interface for extracted herbarium specimen data
**Status**: Production-ready (v1.0)
**GBIF Integration**: Enabled (taxonomy + locality validation)

---

## Quick Start

### Launch Review Interface

```bash
# Basic launch (loads raw.jsonl from extraction directory)
uv run python -m src.review.web_app \
    --extraction-dir full_dataset_processing/openrouter_run_20251010_115131 \
    --port 5002

# With image preview support
uv run python -m src.review.web_app \
    --extraction-dir full_dataset_processing/openrouter_run_20251010_115131 \
    --image-base-url "https://aafc-herbarium.s3.amazonaws.com" \
    --port 5002

# Without GBIF validation (faster for initial review)
uv run python -m src.review.web_app \
    --extraction-dir full_dataset_processing/openrouter_run_20251010_115131 \
    --no-gbif \
    --port 5002
```

**Access**: Open browser to `http://127.0.0.1:5002`

---

## Interface Overview

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│ SPECIMEN REVIEW DASHBOARD                    [Statistics]   │
├─────────────────────────────────────────────────────────────┤
│ Filters: [ Priority ▼ ] [ Status ▼ ] [ Sort: Priority ▼ ]  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌────────────────────────────────────┐  │
│  │              │  │ SPECIMEN: AAFC-12345               │  │
│  │    IMAGE     │  │                                     │  │
│  │   PREVIEW    │  │ catalogNumber: AAFC-12345          │  │
│  │              │  │ scientificName: Rosa acicularis    │  │
│  │              │  │ eventDate: 1985-07-15              │  │
│  │              │  │ recordedBy: J. Smith               │  │
│  └──────────────┘  │                                     │  │
│                    │ [Quality: 68%] [Complete: 85%]     │  │
│  Priority: HIGH    │                                     │  │
│  Quality: 68/100   │ ⚠ Issues:                           │  │
│                    │   - Low confidence: locality (0.42) │  │
│  [Approve] [Reject]│   - GBIF: Name not verified         │  │
│  [Flag for Expert] │                                     │  │
│                    │ [Edit Fields] [GBIF Lookup]        │  │
│  j: Next  k: Prev  │                                     │  │
│  a: Approve        └────────────────────────────────────┘  │
│  r: Reject                                                  │
│  f: Flag                                                    │
└─────────────────────────────────────────────────────────────┘
```

### Keyboard Shortcuts

| Key | Action | Description |
|-----|--------|-------------|
| `j` | Next specimen | Move to next specimen in queue |
| `k` | Previous specimen | Move to previous specimen |
| `a` | Approve | Approve current specimen |
| `r` | Reject | Reject current specimen (prompts for reason) |
| `f` | Flag | Flag for expert review (prompts for notes) |
| `s` | Save edits | Save field corrections |
| `/` | Search | Search by catalog number or scientific name |
| `?` | Help | Show keyboard shortcuts |

---

## Review Workflow

### Step 1: Filter Queue

**Priority-Based Review** (Recommended):
1. Start with CRITICAL priority (missing data, API errors)
2. Move to HIGH priority (low quality, GBIF issues)
3. Address MEDIUM priority (moderate quality)
4. Spot-check LOW/MINIMAL priority

**Status-Based Review**:
- `PENDING`: Not yet reviewed
- `IN_REVIEW`: Currently being reviewed
- `APPROVED`: Ready for publication
- `REJECTED`: Excluded from dataset
- `FLAGGED`: Requires expert attention

### Step 2: Review Specimen

**Check Image** (if available):
- Does extracted data match visible labels?
- Are there illegible sections?
- Are there additional labels not captured?

**Verify Required Fields**:
- ✅ catalogNumber: Present and valid format?
- ✅ scientificName: Taxonomically correct?
- ✅ eventDate: Valid date format (YYYY-MM-DD)?
- ✅ recordedBy: Collector name present?
- ✅ country: Correct country?
- ✅ stateProvince: Valid state/province?
- ✅ locality: Descriptive location?

**Review Quality Indicators**:
- **Quality Score**: Overall specimen quality (0-100)
  - Formula: `(completeness × 0.6) + (confidence × 0.4)`
  - ≥75: High quality
  - 50-74: Moderate quality
  - <50: Low quality, needs attention

- **Completeness Score**: Percentage of required fields present
  - 100%: All 7 required fields populated
  - 71%: 5/7 fields populated
  - <50%: Major gaps in data

- **Confidence Score**: Average AI confidence across fields
  - ≥0.8: High confidence
  - 0.5-0.8: Moderate confidence
  - <0.5: Low confidence, verify against image

### Step 3: GBIF Validation

**Taxonomy Verification**:
- ✅ **Green check**: Name verified in GBIF backbone
- ⚠️ **Yellow warning**: Possible match, low confidence
- ❌ **Red X**: Name not found or invalid

**Common Issues**:
- `fuzzy_match`: Close match but not exact (e.g., spelling variation)
- `synonym`: Name is valid synonym, GBIF suggests accepted name
- `not_found`: Name not in GBIF taxonomy
- `ambiguous`: Multiple possible matches

**Actions**:
- Use "GBIF Lookup" button to search alternatives
- Check if collector used outdated nomenclature
- Verify spelling against image
- Flag for expert if uncertain

### Step 4: Make Decision

**Approve** (Press `a`):
- All required fields present
- Data matches image (if visible)
- GBIF validation passed OR minor issues documented
- Ready for publication

**Reject** (Press `r`):
- Critical data missing (e.g., no scientific name)
- Data clearly incorrect
- Image unreadable, no reliable extraction possible
- Duplicate record

**Flag for Expert** (Press `f`):
- Taxonomic uncertainty requiring specialist
- Unusual locality or date requiring verification
- Conflicting information between labels
- Interesting specimen requiring closer examination

**Edit Fields** (Press `s` after editing):
- Correct obvious OCR errors
- Improve confidence scores with verified data
- Add missing fields visible in image
- Note corrections in "Review Notes"

---

## Priority Levels Explained

### CRITICAL Priority
**Triggers**:
- Extraction completely failed (API error)
- No DWC data returned
- All required fields missing

**Action**: Investigate error logs, consider re-extraction, or mark as unprocessable

**Example**:
```json
{
  "specimen_id": "image_0042.jpg",
  "critical_issues": ["API error: Connection timeout"],
  "dwc_fields": {}
}
```

### HIGH Priority
**Triggers**:
- Quality score < 50%
- Major GBIF validation issues
- Multiple required fields missing
- Very low confidence scores

**Action**: Requires careful manual review and likely corrections

**Example**:
```json
{
  "specimen_id": "image_0123.jpg",
  "quality_score": 42.5,
  "completeness_score": 57.0,
  "gbif_issues": ["scientificName not found in GBIF"],
  "warnings": ["Low confidence for locality: 0.23"]
}
```

### MEDIUM Priority
**Triggers**:
- Quality score 50-75%
- Some required fields missing
- Minor GBIF issues (fuzzy matches)

**Action**: Quick verification, spot corrections

**Example**:
```json
{
  "specimen_id": "image_0234.jpg",
  "quality_score": 64.8,
  "completeness_score": 71.4,
  "gbif_issues": ["fuzzy_match: confidence 0.85"]
}
```

### LOW Priority
**Triggers**:
- Quality score 75-90%
- All required fields present
- Only warnings (no critical issues)

**Action**: Minimal review, spot-check for obvious errors

### MINIMAL Priority
**Triggers**:
- Quality score ≥90%
- Perfect completeness
- GBIF verified
- High confidence across all fields

**Action**: Fast-track approval, quick visual check only

---

## Field-Level Editing

### Edit Workflow

1. Click "Edit Fields" button
2. Modify values in editable text boxes
3. Update confidence if you're certain (0.0-1.0)
4. Add correction notes
5. Click "Save" or press `s`

### Correction Format

**Before**:
```json
{
  "scientificName": {
    "value": "Rosa acicularis",
    "confidence": 0.67
  }
}
```

**After Correction**:
```json
{
  "scientificName": {
    "value": "Rosa acicularis Lindl.",
    "confidence": 1.0,
    "corrected": true,
    "correction_note": "Added authority from image"
  }
}
```

### Best Practices

**DO**:
- ✅ Verify corrections against specimen image
- ✅ Update confidence to 1.0 for human-verified fields
- ✅ Add correction notes explaining changes
- ✅ Use GBIF lookup to verify taxonomic names
- ✅ Preserve original value in notes if drastically different

**DON'T**:
- ❌ Make corrections without image verification
- ❌ Change values without updating confidence
- ❌ Skip correction notes for non-obvious changes
- ❌ "Improve" data beyond what's visible on specimen
- ❌ Guess if label is illegible (mark as uncertain instead)

---

## GBIF Integration Features

### Live Taxonomy Lookup

**Access**: Click "GBIF Lookup" or use API endpoint

**Features**:
- Fuzzy name matching
- Synonym resolution
- Taxonomic hierarchy
- Accepted name suggestions
- Match confidence scores

**Example**:
```bash
curl "http://127.0.0.1:5002/api/gbif/taxonomy?name=Rosa%20acicularis"
```

**Response**:
```json
{
  "record": {
    "scientificName": "Rosa acicularis Lindl.",
    "gbif_taxonKey": "3004387",
    "gbif_acceptedName": "Rosa acicularis Lindl.",
    "gbif_taxonomicStatus": "ACCEPTED"
  },
  "validation": {
    "gbif_taxonomy_verified": true,
    "gbif_confidence": 0.98,
    "gbif_issues": []
  }
}
```

### Name Suggestions

**Access**: Type in search box for autocomplete

**Features**:
- Real-time suggestions as you type
- Ranked by match quality
- Shows accepted names vs synonyms
- Includes common names where available

**Example**:
```bash
curl "http://127.0.0.1:5002/api/gbif/suggest?q=Rosa%20ac&limit=5"
```

### Locality Validation

**When Available**: If specimen has coordinates (decimalLatitude/decimalLongitude)

**Checks**:
- Coordinate validity (valid range)
- Country/province consistency with coordinates
- Known collection localities
- Geocoding suggestions

---

## Quality Metrics Reference

### Completeness Score

**Formula**: `(present_fields / required_fields) × 100`

**Required Fields** (7 total):
1. catalogNumber
2. scientificName
3. eventDate
4. recordedBy
5. country
6. stateProvince
7. locality

**Examples**:
- All 7 fields: 100%
- 6 of 7 fields: 85.7%
- 5 of 7 fields: 71.4%
- 4 of 7 fields: 57.1%

### Confidence Score

**Formula**: `average(confidence_values)`

**Per-Field Confidence**:
- 1.0: Human-verified or perfect OCR
- 0.8-0.99: High AI confidence
- 0.5-0.79: Moderate AI confidence
- 0.0-0.49: Low AI confidence

**Example Calculation**:
```python
fields = {
    "catalogNumber": 0.95,
    "scientificName": 0.72,
    "eventDate": 0.88,
    "recordedBy": 0.54,
    "country": 0.91,
    "stateProvince": 0.67,
    "locality": 0.41
}
confidence_score = sum(fields.values()) / len(fields) = 0.726 (72.6%)
```

### Quality Score

**Formula**: `(completeness × 0.6) + (confidence × 0.4)`

**Rationale**: Completeness weighted higher because missing fields block GBIF publication, while low-confidence fields can be manually verified.

**Example**:
- Completeness: 85% (6/7 fields)
- Confidence: 72.6% (average)
- Quality: `(85 × 0.6) + (72.6 × 0.4) = 51 + 29.04 = 80.04%`

---

## Common Issues & Solutions

### Issue: Image Not Loading

**Symptoms**: Specimen ID shown but image preview blank

**Causes**:
1. `--image-base-url` not configured
2. Image not in S3 bucket
3. S3 bucket not public
4. Network connectivity issues

**Solutions**:
```bash
# 1. Launch with correct base URL
uv run python -m src.review.web_app \
    --extraction-dir <dir> \
    --image-base-url "https://aafc-herbarium.s3.amazonaws.com"

# 2. Verify image exists in S3
aws s3 ls s3://aafc-herbarium/trial_images/image_0001.jpg

# 3. Check S3 bucket public access
aws s3api get-bucket-policy --bucket aafc-herbarium

# 4. Test direct URL
curl -I https://aafc-herbarium.s3.amazonaws.com/trial_images/image_0001.jpg
```

### Issue: GBIF Validation Slow

**Symptoms**: Long delays when loading specimens

**Causes**: GBIF API rate limiting or network latency

**Solutions**:
```bash
# 1. Disable GBIF for initial pass
uv run python -m src.review.web_app --extraction-dir <dir> --no-gbif

# 2. Enable for final validation pass only
# Review and correct major issues first, then re-launch with GBIF
```

### Issue: Too Many CRITICAL Priority Items

**Symptoms**: Queue dominated by failed extractions

**Causes**: API errors, image access issues, /tmp cleanup

**Solutions**:
```bash
# 1. Analyze error patterns
uv run python scripts/analyze_empty_records.py \
    --input full_dataset_processing/openrouter_run_20251010_115131/raw.jsonl \
    --output empty_analysis.json

# 2. Re-extract failed specimens with new caching
uv run python scripts/extract_openrouter.py \
    --input ~/.persistent_cache \
    --output full_dataset_processing/retry_$(date +%Y%m%d) \
    --model qwen-vl-72b-free \
    --failed-only

# 3. After re-extraction, reload review interface
```

### Issue: All Names Failing GBIF Validation

**Symptoms**: Every scientificName shows "not found"

**Causes**:
1. GBIF API connectivity issues
2. Extracted names missing authorities
3. Outdated nomenclature in specimens

**Solutions**:
```bash
# 1. Test GBIF connectivity
curl "https://api.gbif.org/v1/species/match?name=Rosa+acicularis"

# 2. Check if authorities needed
# Some GBIF searches require full name with authority
# Example: "Rosa acicularis" vs "Rosa acicularis Lindl."

# 3. Review extraction prompt
# Consider adding instruction to capture taxonomic authorities
```

---

## API Endpoints Reference

### GET /api/queue

**Purpose**: Get prioritized review queue

**Parameters**:
- `status`: Filter by status (PENDING, IN_REVIEW, APPROVED, REJECTED, FLAGGED)
- `priority`: Filter by priority (CRITICAL, HIGH, MEDIUM, LOW, MINIMAL)
- `sort`: Sort field (priority, quality, completeness)
- `limit`: Max results (default: 100)

**Example**:
```bash
curl "http://127.0.0.1:5002/api/queue?status=pending&priority=high&limit=50"
```

### GET /api/specimen/<id>

**Purpose**: Get full specimen data

**Returns**:
- Complete DWC fields
- Quality metrics
- GBIF validation results
- Review history
- Issues and warnings

**Example**:
```bash
curl "http://127.0.0.1:5002/api/specimen/image_0042.jpg"
```

### PUT /api/specimen/<id>

**Purpose**: Update specimen review

**Body**:
```json
{
  "corrections": {
    "scientificName": {
      "value": "Rosa acicularis Lindl.",
      "confidence": 1.0
    }
  },
  "status": "APPROVED",
  "reviewed_by": "curator_initials",
  "notes": "Verified against image, added authority"
}
```

### POST /api/specimen/<id>/approve

**Purpose**: Quick approve (no corrections)

**Body**:
```json
{
  "reviewed_by": "curator_initials"
}
```

### POST /api/specimen/<id>/reject

**Purpose**: Reject specimen

**Body**:
```json
{
  "reviewed_by": "curator_initials",
  "notes": "Reason for rejection"
}
```

### POST /api/specimen/<id>/flag

**Purpose**: Flag for expert review

**Body**:
```json
{
  "reviewed_by": "curator_initials",
  "notes": "Taxonomic uncertainty - requires specialist"
}
```

### GET /api/statistics

**Purpose**: Get review statistics

**Returns**:
```json
{
  "total_specimens": 549,
  "status_counts": {
    "PENDING": 523,
    "APPROVED": 18,
    "FLAGGED": 8
  },
  "priority_counts": {
    "CRITICAL": 59,
    "HIGH": 142,
    "MEDIUM": 248,
    "LOW": 100
  },
  "avg_quality_score": 64.2,
  "avg_completeness": 68.5,
  "gbif_validated": 312
}
```

### GET /api/export

**Purpose**: Export all reviews to JSON

**Returns**:
```json
{
  "success": true,
  "file": "/path/to/reviews_export.json"
}
```

---

## Batch Review Tips

### Efficient Curation Strategy

**Day 1: Triage** (30-60 min)
1. Filter CRITICAL priority
2. Quick scan - identify patterns in failures
3. Flag systematic issues for bulk fix (e.g., missing API data)
4. Reject obviously unsalvageable specimens

**Day 2: High-Value Review** (2-3 hours)
1. Filter HIGH priority
2. Focus on GBIF validation failures
3. Correct scientific names with lookup
4. Verify locality data

**Day 3: Moderate Quality** (2-3 hours)
1. Filter MEDIUM priority
2. Spot-check for systematic errors
3. Quick corrections where obvious
4. Approve good-enough records

**Day 4: Spot Checks** (30-60 min)
1. Random sample LOW/MINIMAL priority
2. Verify quality metrics accurate
3. Fast-track approvals
4. Export final dataset

### Multi-Curator Workflow

**Curator A: Taxonomic Specialist**
```bash
# Filter flagged items for expert review
curl "http://127.0.0.1:5002/api/queue?status=flagged"
```

**Curator B: Locality Expert**
```bash
# Filter HIGH priority with GBIF locality issues
curl "http://127.0.0.1:5002/api/queue?priority=high" | \
  jq '.queue[] | select(.gbif_verified == false)'
```

**Curator C: Data Quality**
```bash
# Focus on completeness issues
curl "http://127.0.0.1:5002/api/queue?sort=completeness"
```

### Progress Tracking

**Check Statistics Regularly**:
```bash
# Get current status
curl "http://127.0.0.1:5002/api/statistics" | jq

# Calculate remaining work
# pending_count / avg_review_rate = hours_remaining
```

**Export Checkpoints**:
```bash
# Daily backup of review progress
curl "http://127.0.0.1:5002/api/export"
cp full_dataset_processing/*/reviews_export.json \
   backups/reviews_$(date +%Y%m%d).json
```

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                      Flask Web App                          │
│                   (src/review/web_app.py)                   │
├─────────────────────────────────────────────────────────────┤
│                      Review Engine                          │
│                   (src/review/engine.py)                    │
│  - Load extraction results (raw.jsonl)                      │
│  - Calculate quality metrics                                │
│  - Determine review priority                                │
│  - Manage review workflow                                   │
├─────────────────────────────────────────────────────────────┤
│                    GBIF Validator                           │
│                  (src/review/validators.py)                 │
│  - Taxonomy verification                                    │
│  - Locality validation                                      │
│  - Name suggestions                                         │
├─────────────────────────────────────────────────────────────┤
│                      GBIF Module                            │
│                     (qc/gbif.py)                            │
│  - GBIF API integration                                     │
│  - Species lookup                                           │
│  - Geocoding services                                       │
└─────────────────────────────────────────────────────────────┘
         │                       │                      │
         ▼                       ▼                      ▼
    raw.jsonl            GBIF REST API          Browser Client
```

### Data Flow

1. **Initialization**: Load `raw.jsonl` → Parse extraction results → Create SpecimenReview objects
2. **Quality Analysis**: Calculate completeness → Calculate confidence → Identify issues
3. **GBIF Validation**: Verify taxonomy → Check locality → Add metadata
4. **Priority Calculation**: Assess quality score → Determine priority level
5. **Review Queue**: Filter by status/priority → Sort by criteria → Return to UI
6. **User Actions**: Edit fields → Approve/reject → Save corrections → Update status
7. **Export**: Serialize reviews → Save to JSON → Ready for publication

---

## Next Steps After Review

### Export Approved Records

```python
# Load reviews export
import json
with open('reviews_export.json') as f:
    data = json.load(f)

# Filter approved specimens
approved = [
    r for r in data['reviews']
    if r['review']['status'] == 'APPROVED'
]

print(f"Approved: {len(approved)} specimens")
```

### Create DWC Archive

```bash
# Generate Darwin Core Archive for GBIF
uv run python scripts/create_dwc_archive.py \
    --reviews reviews_export.json \
    --output aafc_herbarium_dwc_archive.zip \
    --status APPROVED
```

### Publish to GBIF

```bash
# Validate archive
uv run python scripts/validate_gbif_archive.py \
    --archive aafc_herbarium_dwc_archive.zip

# Upload to GBIF IPT (Interactive Publishing Toolkit)
# See docs/GBIF_PUBLISHING.md for detailed instructions
```

### Quality Report

```bash
# Generate final quality report
uv run python scripts/generate_quality_report.py \
    --reviews reviews_export.json \
    --output final_quality_report.pdf
```

---

## Troubleshooting

### Debug Mode

```bash
# Launch with debug logging
uv run python -m src.review.web_app \
    --extraction-dir <dir> \
    --debug
```

### Check Logs

```bash
# Review Flask logs
tail -f ~/.local/share/herbarium-dwc-extraction/review.log

# Check GBIF API logs
tail -f ~/.local/share/herbarium-dwc-extraction/gbif_validation.log
```

### Reset Review Status

```python
# Reset all specimens to PENDING (fresh start)
from pathlib import Path
from src.review.engine import ReviewEngine

engine = ReviewEngine()
engine.load_extraction_results(Path('raw.jsonl'))

for review in engine.reviews.values():
    review.status = ReviewStatus.PENDING
    review.reviewed_by = None
    review.reviewed_at = None
    review.corrections = {}
    review.notes = None

engine.export_reviews(Path('reviews_reset.json'))
```

---

## Support & Documentation

**Review System**:
- Architecture: `docs/architecture/REVIEW_SYSTEM.md`
- API Reference: This document, "API Endpoints Reference" section
- Code: `src/review/`

**GBIF Integration**:
- Validation Details: `docs/GBIF_VALIDATION.md`
- Publishing Guide: `docs/GBIF_PUBLISHING.md`
- Code: `qc/gbif.py`

**Data Quality**:
- Quality Metrics: `docs/QUALITY_METRICS.md`
- Empty Records Analysis: `scripts/analyze_empty_records.py --help`
- Validation Standards: `docs/TESTING_STANDARDS.md`

**Issues & Questions**:
- GitHub Issues: https://github.com/[repo]/issues
- Email: herbarium-digitization@example.org

---

**Document Version**: 1.0
**Last Updated**: 2025-10-11
**Maintainer**: AAFC Herbarium Digitization Team
