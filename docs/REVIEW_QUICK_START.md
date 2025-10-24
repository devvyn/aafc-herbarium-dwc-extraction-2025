# Manual Review Quick Start Guide

**Purpose**: Start quality-checking extracted Darwin Core data
**Dataset**: v1.0 Vision Baseline (2,702 specimens)
**Quality**: ⚠️ 81% scientificName coverage - needs review
**Time Estimate**: Variable (depends on review depth)

---

## Quick Start: CSV Review (Immediate)

**Best for**: Quick quality assessment, spotting patterns

### Option 1: Spreadsheet Review
```bash
# Open in Excel/Numbers/LibreOffice
open deliverables/v1.0_vision_baseline/occurrence.csv
```

**What to look for**:
- ✅ scientificName: Should be Latin binomial (e.g., "Bouteloua gracilis")
- ❌ Common errors: "Identified by", "Checked by", "Habitab collector"
- ✅ catalogNumber: Numeric codes (e.g., "019121", "1073")
- ❌ Missing data: Empty fields, "0", garbled text
- ✅ eventDate: ISO format YYYY-MM-DD or YYYY
- ❌ OCR errors in dates: "2809" (should be 1980s-2000s range)

### Option 2: Command-Line Preview
```bash
# View first 20 records with column headers
head -20 deliverables/v1.0_vision_baseline/occurrence.csv | column -t -s,

# Count by scientificName
cut -d, -f13 deliverables/v1.0_vision_baseline/occurrence.csv | sort | uniq -c | sort -rn | head -20

# Find empty scientificName fields
grep -n ',,' deliverables/v1.0_vision_baseline/occurrence.csv | head -10
```

---

## Web Interface Review (Recommended)

**Note**: Review interface expects `raw.jsonl` format, but v1.0 only has CSV. You have two options:

### Option A: Review CSV Directly (Faster)
Use spreadsheet or command-line tools above.

### Option B: Web Interface (Future)
Wait for v2.0 OpenRouter extraction which will have full `raw.jsonl` + review interface support.

---

## Focused Review Strategy

### Priority 1: scientificName Field (Most Critical)
**Goal**: Validate 2,343 extracted names (81% coverage)

**Common errors to fix**:
```
❌ "Identified by" → Missing data, extract from label
❌ "Habitab collector" → OCR error, review image
❌ "Checked by" → Wrong field extracted
❌ "Wheat ilield" → OCR misread, verify manually
```

**Validation checklist**:
- [ ] Is it a Latin binomial? (Genus species)
- [ ] Does it match visible label text?
- [ ] Is authority citation present? (optional but good)
- [ ] Any obvious OCR errors? (misspellings, wrong letters)

### Priority 2: catalogNumber Field (Critical Gap)
**Goal**: Improve 915 records (32% coverage) → target 80%+

**Why this matters**: Catalog numbers are primary keys for institutional databases.

**What to look for**:
- Check specimen images for catalog numbers
- Often in format: "019121", "AAFC 1073", "280628"
- May be stamped, handwritten, or printed labels
- Sometimes abbreviated: "Cat. No.", "No.", "#"

**If missing in extraction**:
- Note image filename
- Add catalog number from visual inspection
- Document in correction log

### Priority 3: Collector & Date (Moderate Priority)
**Current coverage**:
- recordedBy: 10.3% (296/2,885) - VERY LOW
- eventDate: 63.6% (1,836/2,885) - MODERATE

**Strategy**: Focus on specimens with high scientific value first (rare species, type specimens).

---

## Quality Metrics to Track

### Before Review (Baseline)
```json
{
  "scientificName": "81.2% coverage",
  "catalogNumber": "31.7% coverage",
  "total_reviewed": 0,
  "corrections_made": 0
}
```

### After Review (Target)
```json
{
  "scientificName": "95%+ coverage (after corrections)",
  "catalogNumber": "80%+ coverage (after additions)",
  "total_reviewed": 2702,
  "corrections_made": "~500-1000 (estimated)"
}
```

---

## Workflow: Iterative Review Cycles

### Cycle 1: Spot Check (30-60 minutes)
**Sample size**: 50-100 records
**Goal**: Understand error patterns

```bash
# Random sample
shuf -n 50 deliverables/v1.0_vision_baseline/occurrence.csv > review_sample_50.csv
open review_sample_50.csv
```

**Document**:
- What % have scientificName errors?
- What % are missing catalogNumber?
- Common OCR error patterns?

### Cycle 2: High-Value Specimens (2-4 hours)
**Focus**: Rare species, complete data, good quality images
**Goal**: Get 200-300 high-quality records publication-ready

**Filter criteria**:
- Has scientificName AND catalogNumber
- High OCR confidence (>0.9)
- Readable labels in image

### Cycle 3: Fill Critical Gaps (4-8 hours)
**Focus**: Add missing catalogNumber, fix scientificName errors
**Goal**: Bring coverage to publication thresholds

---

## Tools for Efficient Review

### 1. GBIF Name Matching
```bash
# Check if scientificName is valid
curl "https://api.gbif.org/v1/species/match?name=Bouteloua%20gracilis"
```

### 2. Batch Validation Script (Future)
```bash
# Validate all scientificNames against GBIF
uv run python scripts/validate_names_gbif.py \
  --input deliverables/v1.0_vision_baseline/occurrence.csv \
  --output validation_report.json
```

### 3. Image Viewer (for manual inspection)
```bash
# View specimen image by SHA256 hash
# Images are in S3 or local cache
# Hash is in specimen_id column
```

---

## Correction Workflow

### Option 1: Direct CSV Editing
1. Open `deliverables/v1.0_vision_baseline/occurrence.csv`
2. Make corrections
3. Save as `occurrence_reviewed_YYYYMMDD.csv`
4. Document changes in `REVIEW_LOG.md`

### Option 2: Correction Script (Future)
```bash
# Interactive correction tool
uv run python scripts/correct_interactive.py \
  --input deliverables/v1.0_vision_baseline/occurrence.csv \
  --output corrected/
```

---

## Expected Review Time

**Realistic estimates**:
- **Quick scan** (all 2,702 records): 2-3 hours
- **Light review** (fix obvious errors): 8-12 hours
- **Thorough review** (validate + fill gaps): 40-60 hours
- **Complete validation** (100% verified): 80-120 hours

**Recommendation**: Start with quick scan, prioritize high-value specimens, decide depth based on publication timeline.

---

## When to Stop Reviewing v1.0

**Consider switching to v2.0 OpenRouter if**:
- Error rate > 30% (more efficient to re-extract than fix)
- Missing catalogNumber rate > 50% (v2.0 expected >90%)
- Review time > 20 hours (v2.0 extraction takes 4-6 hours)

**v2.0 advantages**:
- 100% scientificName validated (vs 81% v1.0)
- >90% catalogNumber expected (vs 32% v1.0)
- Fewer errors = less review time
- Still FREE (same cost as v1.0)

---

## Next Steps

1. **Immediate**: Start CSV review with spreadsheet or command-line
2. **Document findings**: Create `REVIEW_LOG.md` in deliverables/v1.0_vision_baseline/
3. **Decide strategy**:
   - Continue v1.0 review if error rate acceptable?
   - OR trigger v2.0 OpenRouter extraction for higher quality baseline?

---

**Questions?** See [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md) (coming soon)

**Last Updated**: 2025-10-24
