# Apple Vision Deployment Guide - Process 2,800 Specimens

**Quick deployment instructions for processing the captured herbarium specimens using Apple Vision OCR (95% accuracy).**

## Prerequisites

- **macOS system** (required for Apple Vision)
- **2,800 specimen photos** organized in a directory
- **Project installed** (`./bootstrap.sh` completed)
- **Sufficient disk space** (estimate 500MB-1GB for output databases)

## Deployment Steps

### 1. Verify Apple Vision is Available

```bash
# Check OCR engines
python cli.py check-deps --engines vision

# Expected output:
# ✅ Apple Vision: Available (macOS native)
```

### 2. Organize Your 2,800 Photos

```bash
# Create consistent directory structure
mkdir -p ~/herbarium_processing/input
mkdir -p ~/herbarium_processing/output

# Move your 2,800 photos to input directory
# (adjust path to your actual photo location)
cp /path/to/your/2800/photos/* ~/herbarium_processing/input/
```

### 3. Start Apple Vision Processing

```bash
# Navigate to project directory
cd /Users/devvynmurphy/Documents/GitHub/aafc-herbarium-dwc-extraction-2025

# Start processing with Apple Vision
python cli.py process \
  --input ~/herbarium_processing/input \
  --output ~/herbarium_processing/output \
  --engine vision \
  --config config/config.default.toml

# Processing will show progress like:
# Processing specimen 1/2800: specimen_001.jpg
# Apple Vision confidence: 0.94
# Processing specimen 2/2800: specimen_002.jpg
# Apple Vision confidence: 0.96
```

**Processing time estimate**: 2-4 hours for 2,800 images (varies by image size)

### 4. Monitor Progress

```bash
# In another terminal, check progress
python cli.py stats --db ~/herbarium_processing/output/app.db

# View processing status
sqlite3 ~/herbarium_processing/output/app.db "SELECT status, COUNT(*) FROM specimens GROUP BY status;"
```

### 5. Handle Interruptions (Resume if needed)

```bash
# If processing gets interrupted, resume from where it left off
python cli.py resume \
  --input ~/herbarium_processing/input \
  --output ~/herbarium_processing/output \
  --engine vision
```

## Expected Results

### Output Files Generated

After processing 2,800 specimens, you'll have:

```
~/herbarium_processing/output/
├── occurrence.csv           # 2,800 Darwin Core records
├── identification_history.csv # Taxonomic data
├── raw.jsonl               # Complete OCR results log
├── manifest.json           # Processing metadata
├── candidates.db           # SQLite database for review
├── app.db                  # Processing status database
└── images/                 # Thumbnail cache
```

### Quality Expectations (Based on Research)

- **95% accuracy** on clear specimen labels
- **~2,660 specimens** (95%) will need minimal or no manual review
- **~140 specimens** (5%) may need manual correction
- **High confidence** on institutional names, scientific names, collectors, dates

### Data Volume Estimates

- **occurrence.csv**: ~500KB-1MB (2,800 records)
- **raw.jsonl**: ~5-10MB (complete OCR logs)
- **candidates.db**: ~50-100MB (all OCR results)
- **app.db**: ~20-50MB (processing metadata)

## Quality Control Workflow

### 1. Review High-Confidence Results

```bash
# Launch web review interface
python review_web.py \
  --db ~/herbarium_processing/output/candidates.db \
  --images ~/herbarium_processing/input \
  --port 8080

# Open browser to http://localhost:8080
```

### 2. Focus on Low-Confidence Cases

```bash
# Review only specimens needing attention (confidence < 80%)
python review_web.py \
  --db ~/herbarium_processing/output/candidates.db \
  --images ~/herbarium_processing/input \
  --filter "confidence < 0.8"
```

### 3. Export for Institutional Review

```bash
# Create Excel file for curatorial review
python export_review.py \
  --db ~/herbarium_processing/output/app.db \
  --format xlsx \
  --output ~/herbarium_processing/institutional_review.xlsx
```

## Production Handover Package

### Generate Complete Dataset

```bash
# Create versioned Darwin Core Archive
python cli.py archive \
  --output ~/herbarium_processing/output \
  --version 1.0.0 \
  --include-multimedia \
  --filter "confidence > 0.7"

# Results in: ~/herbarium_processing/output/dwca_v1.0.0.zip
```

### Quality Report

```bash
# Generate comprehensive quality report
python qc/comprehensive_qc.py \
  --db ~/herbarium_processing/output/app.db \
  --output ~/herbarium_processing/qc_report.html \
  --include-geographic-validation \
  --include-taxonomic-validation
```

## Troubleshooting

### Common Issues

**Processing stops with errors:**
```bash
# Check logs
tail -f ~/herbarium_processing/output/processing.log

# Resume processing
python cli.py resume --input ~/herbarium_processing/input --output ~/herbarium_processing/output
```

**Low confidence results:**
- Apple Vision typically achieves 95% accuracy
- If seeing lower confidence, check image quality
- Consider preprocessing for damaged/blurry specimens

**Out of disk space:**
```bash
# Check disk usage
df -h ~/herbarium_processing/

# Clean up intermediate files if needed
rm -rf ~/herbarium_processing/output/temp/
```

## Success Metrics

- **2,800 specimens processed**: 100% completion
- **Average confidence > 0.90**: Meeting 95% accuracy target
- **< 5% manual review needed**: ~140 specimens or fewer
- **Darwin Core compliance**: Ready for GBIF submission
- **Processing time < 4 hours**: Efficient automated workflow

## Next Steps After Processing

1. **Institutional Review**: Use generated Excel files for curatorial review
2. **GBIF Submission**: Submit dwca_v1.0.0.zip to GBIF
3. **Data Archival**: Store complete results package
4. **Documentation**: Update institutional procedures based on workflow

---

**Contact**: Open [GitHub issue](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues) for deployment support.