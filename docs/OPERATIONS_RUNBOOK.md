# Operations Runbook - Herbarium Extraction Pipeline

**Purpose**: Complete operational guide for running specimen extractions
**Audience**: Successor maintainers, future operators
**Scope**: From image acquisition through GBIF publication

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [System Overview](#system-overview)
3. [Standard Operating Procedures](#standard-operating-procedures)
4. [Quality Assurance](#quality-assurance)
5. [Troubleshooting](#troubleshooting)
6. [Performance Optimization](#performance-optimization)

---

## Quick Reference

### Common Operations

```bash
# Process new specimens (OpenRouter - FREE, high quality)
cd ~/Documents/GitHub/aafc-herbarium-dwc-extraction-2025
uv run python scripts/extract_openrouter.py \
  --input /path/to/images \
  --output ./deliverables/vX.X_description/raw \
  --model qwen-vl-72b-free

# Generate quality report
uv run python scripts/analyze_quality.py \
  --input ./deliverables/vX.X/raw \
  --output ./deliverables/vX.X/quality_report.json

# Create GBIF export
uv run python cli.py export \
  --output ./deliverables/vX.X \
  --version X.X.X \
  --compress

# Launch review interface
uv run python cli.py review \
  --extraction-dir ./deliverables/vX.X \
  --port 5002
```

### Emergency Contacts
- **Scientific Validation**: Dr. Julia Leeson (Herbarium Manager)
- **Technical Issues**: GitHub Issues
- **Documentation**: https://aafc.devvyn.ca

---

## System Overview

### Architecture
```
┌─────────────┐
│ S3 Storage  │ 2,885 specimen images
└──────┬──────┘
       │ fetch
       ▼
┌─────────────┐
│ Extraction  │ OpenRouter Qwen 2.5 VL (FREE)
└──────┬──────┘
       │ extract
       ▼
┌─────────────┐
│ Darwin Core │ occurrence.csv (GBIF format)
└──────┬──────┘
       │ review
       ▼
┌─────────────┐
│ Publication │ GBIF via Canadensys
└─────────────┘
```

### Components
- **Image Storage**: AWS S3 (devvyn.aafc-srdc.herbarium bucket)
- **Extraction Engine**: OpenRouter API (Qwen 2.5 VL 72B Instruct)
- **Data Format**: Darwin Core Archive (DwC-A)
- **Review Interface**: Quart web application (async)
- **Output**: `deliverables/vX.X/` versioned datasets

---

## Standard Operating Procedures

### SOP 1: Processing New Specimens

**Trigger**: New specimen images available in S3

**Prerequisites**:
- [ ] S3 access configured (~/.aws/credentials)
- [ ] OpenRouter API key loaded (~/Secrets/approved-for-agents/)
- [ ] Python environment active (uv)

**Steps**:

#### 1. Verify Image Count
```bash
# Count images in S3 manifest
wc -l ~/Documents/GitHub/s3-image-dataset-kit/manifests/inventory-v1.jsonl

# Expected: 2,885 lines (one per specimen)
```

#### 2. Create Version Directory
```bash
# Semantic versioning: vMAJOR.MINOR_description
# Major: Significant extraction method change
# Minor: Same method, different dataset or config
mkdir -p deliverables/v2.1_new_specimens
```

#### 3. Run Extraction
```bash
cd ~/Documents/GitHub/aafc-herbarium-dwc-extraction-2025

uv run python scripts/extract_openrouter.py \
  --input ~/Documents/GitHub/s3-image-dataset-kit/cache \
  --output ./deliverables/v2.1_new_specimens/raw \
  --model qwen-vl-72b-free
```

**Expected output**:
```
✅ Loaded 2885 images
🔬 Processing with qwen/qwen-2.5-vl-72b-instruct:free
Progress: 100% |████████████████████| 2885/2885
⏱️  Completed in 4h 23m
💰 Cost: $0.00 (FREE tier)
📊 Success rate: 99.8% (2880/2885)
```

#### 4. Generate Quality Report
```bash
uv run python scripts/analyze_quality.py \
  --input ./deliverables/v2.1_new_specimens/raw \
  --output ./deliverables/v2.1_new_specimens/quality_report.json
```

**Quality thresholds**:
- ✅ Minimum: ≥75% scientificName
- ✅ Good: ≥90% scientificName, ≥80% catalogNumber
- ✅ Excellent: ≥98% scientificName, ≥95% catalogNumber

#### 5. Review Data Quality
```bash
# Launch review interface
uv run python cli.py review \
  --extraction-dir ./deliverables/v2.1_new_specimens \
  --port 5002

# Open browser: http://127.0.0.1:5002
```

**Review focus**:
- Scientific name accuracy (Latin binomials)
- Catalog number presence and correctness
- Date format (ISO 8601: YYYY-MM-DD)
- Collector names (complete, not OCR fragments)

#### 6. Export for GBIF
```bash
uv run python cli.py export \
  --output ./deliverables/v2.1_new_specimens \
  --version 2.1.0 \
  --format rich \
  --compress

# Creates: deliverables/v2.1_new_specimens/dwca_v2.1.0_*.zip
```

#### 7. Document & Commit
```bash
# Add quality warning if needed
cp docs/templates/QUALITY_WARNING_template.md \
   deliverables/v2.1_new_specimens/QUALITY_WARNING.md

# Edit with actual metrics

# Commit metadata (data files ignored by .gitignore)
git add deliverables/v2.1_new_specimens/*.json \
        deliverables/v2.1_new_specimens/*.md \
        deliverables/README.md
git commit -m "data: Add v2.1 extraction metadata

- 2,885 specimens processed
- OpenRouter Qwen 2.5 VL 72B (FREE)
- scientificName: 98.2% coverage
- catalogNumber: 91.4% coverage
- Ready for stakeholder review"
git push
```

**Duration**: ~5-6 hours (4h extraction + 1h QA/export)

---

### SOP 2: GBIF Publication via Canadensys

**Trigger**: Quality-validated dataset ready for publication

**Prerequisites**:
- [ ] Dataset meets quality thresholds (≥90% scientificName)
- [ ] Scientific validation complete (Dr. Leeson approval)
- [ ] Darwin Core Archive exported
- [ ] Canadensys IPT account access

**Steps**:

#### 1. Prepare DwC-A Package
```bash
# Extract DwC-A contents for upload
unzip deliverables/vX.X/dwca_vX.X.0_*.zip -d /tmp/dwca_upload

# Verify required files
ls /tmp/dwca_upload/
# Expected:
#   meta.xml (archive descriptor)
#   eml.xml (metadata)
#   occurrence.txt (Darwin Core records)
```

#### 2. Upload to Canadensys IPT
```
Portal: https://data.canadensys.net/ipt/
Login: [AAFC institutional account]

Steps:
1. Click "Create new resource"
2. Resource shortname: aafc-herbarium-saskatchewan-YYYYMM
3. Resource type: "Occurrence"
4. Upload: occurrence.txt
5. Map fields to Darwin Core terms (auto-detected)
6. Upload: eml.xml (metadata)
7. Validate mappings
8. Publish to GBIF
```

#### 3. Monitor Publication
```
GBIF typically processes datasets within 24-48 hours.

Check status:
1. IPT dashboard: https://data.canadensys.net/ipt/manage/
2. GBIF dataset page: https://www.gbif.org/dataset/[dataset-key]
```

#### 4. Record DOI
```bash
# GBIF assigns DOI for citation
# Update deliverables/vX.X/DATA_DOI.txt

echo "10.15468/abc123" > deliverables/vX.X/DATA_DOI.txt
git add deliverables/vX.X/DATA_DOI.txt
git commit -m "data: Add GBIF DOI for v${VERSION}"
```

**Duration**: ~2-3 hours (upload + validation)

---

### SOP 3: Incremental Updates (New Specimens)

**Scenario**: Add 500 new specimens to existing 2,885

**Approach**: Process separately, then merge or publish as supplement

#### Option A: Separate Version
```bash
# Create v2.2 with only new specimens
mkdir -p deliverables/v2.2_supplement_2025_batch2

# Process 500 new images
uv run python scripts/extract_openrouter.py \
  --input /path/to/new_images \
  --output ./deliverables/v2.2_supplement_2025_batch2/raw \
  --model qwen-vl-72b-free

# Publish as separate GBIF dataset: "AAFC Herbarium - 2025 Batch 2"
```

#### Option B: Merged Version
```bash
# Combine v2.1 (2,885) + v2.2 (500) = v3.0 (3,385)
cat deliverables/v2.1/occurrence.csv \
    deliverables/v2.2/occurrence.csv > \
    deliverables/v3.0_complete_2025/occurrence.csv

# Re-export and publish as superseding dataset
```

**Recommendation**: Option A (separate) for clear provenance, Option B (merged) for single institutional dataset.

---

## Quality Assurance

### Pre-Flight Checks

Before starting extraction:
```bash
# 1. Verify S3 access
aws s3 ls s3://devvyn.aafc-srdc.herbarium/images/ --region ca-central-1

# 2. Test OpenRouter API
python -c "
import os, sys
sys.path.insert(0, str(Path.home() / 'Secrets' / 'approved-for-agents'))
from load_keys import load_api_keys
load_api_keys()
print('✅ OpenRouter key loaded' if os.environ.get('OPENROUTER_API_KEY') else '❌ No key')
"

# 3. Verify disk space (need ~500MB for extraction)
df -h .

# 4. Check Python environment
uv run python --version
# Expected: Python 3.11+
```

### Post-Extraction Validation

Automated checks:
```bash
# Run full validation suite
uv run python -m pytest tests/ -v

# Check Darwin Core field coverage
uv run python scripts/validate_dwc_coverage.py \
  --input deliverables/vX.X/occurrence.csv \
  --minimum-coverage 0.75

# Validate against GBIF requirements
uv run python scripts/validate_gbif.py \
  --input deliverables/vX.X/occurrence.csv
```

Manual spot checks:
- [ ] Sample 50 random records visually
- [ ] Verify Latin binomials in scientificName
- [ ] Check catalog number format consistency
- [ ] Validate date ranges (1900-2025 expected)
- [ ] Confirm country=Canada, stateProvince=Saskatchewan

---

## Troubleshooting

See [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md) for detailed solutions.

### Common Issues Quick Reference

**Extraction fails with "API key not found"**
```bash
# Solution: Reload API keys
cd ~/Secrets/approved-for-agents
source load-env.sh
```

**Low scientificName coverage (<80%)**
```bash
# Possible causes:
# - Poor image quality (check sample images)
# - Wrong extraction model (use qwen-vl-72b-free)
# - OCR confidence threshold too high

# Check quality_report.json for patterns
jq '.field_coverage.scientificName' deliverables/vX.X/quality_report.json
```

**Review interface won't start**
```bash
# Check port availability
lsof -i :5002

# Use alternative port
uv run python cli.py review --extraction-dir deliverables/vX.X --port 5003
```

---

## Performance Optimization

### Processing Speed

**Current**: ~4-6 hours for 2,885 specimens (OpenRouter)

**Optimization options**:
1. **Batch processing**: Split into chunks, process parallel (if multiple API keys)
2. **Resume capability**: Use `--offset` flag if interrupted
3. **Cache warming**: Pre-fetch images from S3 before extraction

```bash
# Resume from specimen 1000
uv run python scripts/extract_openrouter.py \
  --input /path/to/images \
  --output ./deliverables/vX.X/raw \
  --model qwen-vl-72b-free \
  --offset 1000 \
  --limit 1885  # Process remaining (2885-1000)
```

### Cost Management

**OpenRouter FREE tier**:
- Model: qwen/qwen-2.5-vl-72b-instruct:free
- Cost: $0.00 unlimited
- Quality: >98% scientificName validated

**Paid fallback** (if FREE tier unavailable):
- Model: GPT-4o-mini ($3-4 per 1000 specimens)
- Use only if FREE tier rate-limited

---

## Appendix

### File Locations Reference
```
~/Documents/GitHub/aafc-herbarium-dwc-extraction-2025/
├── deliverables/           # Canonical data repository
│   ├── v1.0_vision_baseline/
│   ├── v2.0_openrouter_production/
│   └── vX.X_description/   # Future versions
├── docs/                   # Documentation
│   ├── OPERATIONS_RUNBOOK.md (this file)
│   ├── TROUBLESHOOTING_GUIDE.md
│   └── REVIEW_QUICK_START.md
├── scripts/                # Automation tools
│   ├── extract_openrouter.py
│   ├── analyze_quality.py
│   └── validate_*.py
└── cli.py                  # Main command interface
```

### Version Numbering Scheme
- **v1.X**: Apple Vision API (baseline quality, 81% scientificName)
- **v2.X**: OpenRouter high-quality (98%+ scientificName)
- **v3.X**: Future ensemble/validated methods

### Quality Tier Definitions
- **Baseline (C)**: 75-85% scientificName, suitable for exploration
- **Good (B)**: 86-95% scientificName, suitable for institutional use
- **Excellent (A)**: 96-100% scientificName, publication-ready

---

**Maintained by**: AAFC Herbarium Digitization Project
**Last Updated**: 2025-10-24
**Version**: 1.0
**Next Review**: After v2.1 production run or 6 months
