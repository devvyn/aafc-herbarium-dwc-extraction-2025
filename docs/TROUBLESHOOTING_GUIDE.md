# Troubleshooting Guide

**Purpose**: Solutions to common issues in herbarium extraction pipeline
**Audience**: Operators, maintainers, future developers
**Related**: See [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md) for standard procedures

---

## Table of Contents

1. [Extraction Issues](#extraction-issues)
2. [Quality Problems](#quality-problems)
3. [API & Authentication](#api--authentication)
4. [Review Interface](#review-interface)
5. [Export & Publication](#export--publication)
6. [Performance Issues](#performance-issues)

---

## Extraction Issues

### ❌ Problem: "ModuleNotFoundError: No module named 'openai'"

**Symptom**:
```
Traceback (most recent call last):
  File "scripts/extract_openrouter.py", line 12, in <module>
    import openai
ModuleNotFoundError: No module named 'openai'
```

**Cause**: Python environment not activated or dependencies not installed

**Solution**:
```bash
# Reinstall dependencies
cd ~/Documents/GitHub/aafc-herbarium-dwc-extraction-2025
uv sync

# Verify installation
uv run python -c "import openai; print('✅ openai installed')"
```

**Prevention**: Always use `uv run python` instead of bare `python`

---

### ❌ Problem: Extraction stops midway (network timeout)

**Symptom**:
```
Processing: 1234/2885 specimens...
Error: Request timeout after 30s
```

**Cause**: Network interruption or API server slowness

**Solution**: Resume from last successful specimen
```bash
# Check last processed specimen number
tail -100 extraction.log | grep "Success"

# Resume from next specimen
uv run python scripts/extract_openrouter.py \
  --input /path/to/images \
  --output ./deliverables/vX.X/raw \
  --model qwen-vl-72b-free \
  --offset 1234  # Last successful + 1
```

**Prevention**: Run in `screen` or `tmux` for long processes
```bash
# Start persistent session
screen -S extraction

# Run extraction
uv run python scripts/extract_openrouter.py ...

# Detach: Ctrl+A, then D
# Reattach later: screen -r extraction
```

---

### ❌ Problem: Empty scientificName fields (>50% missing)

**Symptom**:
```json
{
  "scientificName_coverage": 0.45,  // Only 45% coverage
  "empty_fields": 1588
}
```

**Cause**: Wrong extraction model or poor image quality

**Diagnosis**:
```bash
# Check which model was used
cat deliverables/vX.X/extraction_metadata.json | jq '.config.model'

# Sample images to verify quality
ls /path/to/images | head -10 | xargs -I {} open {}
```

**Solutions**:

**If using wrong model** (e.g., text-only instead of vision):
```bash
# Re-extract with correct vision model
uv run python scripts/extract_openrouter.py \
  --model qwen-vl-72b-free  # Vision model
```

**If images are poor quality**:
- Check specimen photography (focus, lighting, resolution)
- Pre-process images (contrast enhancement, rotation correction)
- Consider manual transcription for critical specimens

**If model is correct**:
- Spot-check 20 random images - are labels readable by human?
- If YES: File issue, may need model fine-tuning
- If NO: Re-photograph specimens

---

## Quality Problems

### ⚠️ Problem: Scientific names contain non-Latin text

**Symptom**:
```csv
scientificName
"Identified by"
"Checked by"
"Habitab collector"
```

**Cause**: OCR extracted wrong label section

**Quick Fix**: Manual correction in CSV
```bash
# Find all invalid scientificName entries
grep -n "Identified by\|Checked by" deliverables/vX.X/occurrence.csv

# Edit CSV, replace with actual name from image
```

**Long-term Solution**: Improve extraction prompt
```python
# In scripts/extract_openrouter.py, enhance prompt:
prompt = """
Extract ONLY the Latin binomial from the specimen label.
IGNORE fields like "Identified by", "Checked by", "Collector".
Scientific name format: Genus species (optional author)
Example: Bouteloua gracilis (HBK.) Lag.
"""
```

---

### ⚠️ Problem: Catalog numbers missing (low coverage)

**Symptom**:
```json
{
  "catalogNumber_coverage": 0.32  // Only 32% extracted
}
```

**Cause**: Catalog numbers have inconsistent format across labels

**Diagnosis**:
```bash
# View catalog number patterns in successful extractions
cut -d, -f2 deliverables/vX.X/occurrence.csv | grep -v "^$" | sort | uniq -c | head -20
```

**Common patterns**:
- Numeric only: `019121`, `1073`
- Prefixed: `AAFC 280628`, `Cat. No. 433`
- Stamped: Often in top-right corner of label

**Solution**: Manual addition from images
```bash
# Create catalog number mapping
# image_id,catalogNumber
# abc123,019121
# def456,1073

# Merge into main dataset
python scripts/merge_catalog_numbers.py \
  --input deliverables/vX.X/occurrence.csv \
  --catalog-map catalog_additions.csv \
  --output deliverables/vX.X/occurrence_updated.csv
```

---

### ⚠️ Problem: Dates in wrong format (GBIF validation fails)

**Symptom**:
```
GBIF Validator: eventDate must be ISO 8601 (YYYY-MM-DD)
Found: "2809", "Aug 14, 1969", "1960's"
```

**Cause**: Varied date formats on labels, OCR artifacts

**Solution**: Batch normalize dates
```bash
# Run date normalization script
uv run python scripts/normalize_dates.py \
  --input deliverables/vX.X/occurrence.csv \
  --output deliverables/vX.X/occurrence_normalized.csv

# Handles:
# "Aug 14, 1969" → "1969-08-14"
# "1960's" → "1960"
# "2809" → Flag for manual review (likely OCR error)
```

**Manual corrections**:
```csv
# Before
eventDate: "2809"

# After (inspect image, likely 1980 or 2008)
eventDate: "1980"  # OR mark as uncertain: "1980?"
```

---

## API & Authentication

### ❌ Problem: "API key not found" error

**Symptom**:
```
Error: OPENROUTER_API_KEY environment variable not set
```

**Cause**: API key not loaded into environment

**Solution**:
```bash
# Load API keys
cd ~/Secrets/approved-for-agents
source load-env.sh

# Verify loaded
echo ${OPENROUTER_API_KEY:0:20}...  # Should show first 20 chars

# Run extraction in same shell
cd ~/Documents/GitHub/aafc-herbarium-dwc-extraction-2025
uv run python scripts/extract_openrouter.py ...
```

**Prevention**: Add to shell startup (~/.zshrc)
```bash
# Auto-load API keys for herbarium work
alias herbarium='cd ~/Documents/GitHub/aafc-herbarium-dwc-extraction-2025 && source ~/Secrets/approved-for-agents/load-env.sh'
```

---

### ❌ Problem: "Rate limit exceeded" (429 error)

**Symptom**:
```
Error 429: Rate limit exceeded. Please try again in 60 seconds.
```

**Cause**: FREE tier rate limits (rare but possible)

**Immediate solution**: Wait and retry
```bash
# Extraction script auto-retries with exponential backoff
# No action needed, just wait

# Or manually resume later
uv run python scripts/extract_openrouter.py \
  --offset 1234  # Where it stopped
```

**Alternative**: Switch to paid model temporarily
```bash
uv run python scripts/extract_openrouter.py \
  --model qwen-vl-72b  # Paid tier (fast, costs ~$0.10/1000)
```

**Long-term**: Spread processing across multiple days if consistent

---

### ❌ Problem: S3 access denied

**Symptom**:
```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**Cause**: AWS credentials not configured or expired

**Solution**:
```bash
# Check AWS credentials
cat ~/.aws/credentials

# If empty or expired, reconfigure
aws configure
# Access Key: [from AAFC IT]
# Secret Key: [from AAFC IT]
# Region: ca-central-1
```

**Test S3 access**:
```bash
aws s3 ls s3://devvyn.aafc-srdc.herbarium/images/ --region ca-central-1
# Should list images
```

---

## Review Interface

### ❌ Problem: Review interface won't start (port already in use)

**Symptom**:
```
Error: Address already in use (port 5002)
```

**Cause**: Another process using port 5002

**Solution 1**: Find and kill existing process
```bash
# Find process on port 5002
lsof -i :5002

# Kill process
kill -9 [PID]
```

**Solution 2**: Use different port
```bash
uv run python cli.py review \
  --extraction-dir deliverables/vX.X \
  --port 5003  # Alternative port
```

---

### ⚠️ Problem: Images not loading in review interface

**Symptom**: Specimen images show as broken links

**Cause**: Image path mismatch (local vs S3)

**Diagnosis**:
```bash
# Check image_base_url in review config
grep "image_base_url" deliverables/vX.X/extraction_metadata.json
```

**Solution**: Specify correct image base URL
```bash
# For S3 images
uv run python cli.py review \
  --extraction-dir deliverables/vX.X \
  --image-base-url "https://s3.ca-central-1.amazonaws.com/devvyn.aafc-srdc.herbarium/images/"

# For local cache
uv run python cli.py review \
  --extraction-dir deliverables/vX.X \
  --image-base-url "file:///Users/[user]/Documents/GitHub/s3-image-dataset-kit/cache/"
```

---

## Export & Publication

### ❌ Problem: GBIF validator rejects Darwin Core Archive

**Symptom**:
```
GBIF Validator Errors:
- Required field 'basisOfRecord' missing
- scientificName contains invalid characters
- eventDate not ISO 8601 format
```

**Solution**: Run pre-publication validation
```bash
# Validate before uploading to GBIF
uv run python scripts/validate_gbif.py \
  --input deliverables/vX.X/occurrence.csv \
  --fix-errors \
  --output deliverables/vX.X/occurrence_gbif_valid.csv

# Re-export with validated data
uv run python cli.py export \
  --output deliverables/vX.X \
  --version X.X.X \
  --compress
```

**Common fixes**:
- Add basisOfRecord: "PreservedSpecimen" (required)
- Remove non-ASCII characters from scientificName
- Normalize dates to YYYY-MM-DD
- Add country: "Canada" if missing

---

### ⚠️ Problem: EML metadata generation fails

**Symptom**:
```
Error: Missing required EML field: 'creator.organizationName'
```

**Cause**: Metadata template incomplete

**Solution**: Manually edit EML template
```bash
# Copy template
cp templates/eml_template.xml deliverables/vX.X/eml.xml

# Edit required fields
# - creator.organizationName: "Agriculture and Agri-Food Canada"
# - title: "AAFC Herbarium Collection - Saskatchewan [YYYY]"
# - abstract: [Dataset description]

# Validate EML
uv run python scripts/validate_eml.py \
  --input deliverables/vX.X/eml.xml
```

---

## Performance Issues

### 🐌 Problem: Extraction very slow (>8 hours for 2,885 specimens)

**Expected**: 4-6 hours for 2,885 specimens with OpenRouter

**Diagnosis**:
```bash
# Check processing rate
tail -f extraction.log | grep "specimens/hour"
```

**Common causes**:

**1. Network throttling**
```bash
# Test network speed to OpenRouter
time curl -s https://openrouter.ai/api/v1/models | head
# Should respond < 1 second
```

**2. Large image files**
```bash
# Check average image size
du -sh /path/to/images/ | awk '{print $1}'
# Expected: ~100-200KB per image

# If images >1MB each, resize first
mogrify -resize 2000x2000\> -quality 85 /path/to/images/*.jpg
```

**3. Model choice**
```bash
# Ensure using fast FREE model
grep "model.*qwen-vl-72b-free" extraction.log

# If using paid/slower model, switch
uv run python scripts/extract_openrouter.py \
  --model qwen-vl-72b-free  # Fastest FREE option
```

---

### 💾 Problem: Disk space full during extraction

**Symptom**:
```
Error: No space left on device
```

**Cause**: Cache directory filling up

**Immediate fix**:
```bash
# Clear old cache
rm -rf ~/.cache/herbarium-extraction/*

# Free space check
df -h .
```

**Prevention**: Clean cache between runs
```bash
# Add to extraction script
uv run python scripts/extract_openrouter.py \
  --cache-dir /tmp/herbarium_cache  # Uses system temp (auto-cleaned)
```

---

## Diagnostic Commands

### System Health Check
```bash
#!/bin/bash
echo "=== Herbarium Pipeline Health Check ==="

echo "✓ Python version:"
uv run python --version

echo "✓ Disk space:"
df -h . | tail -1

echo "✓ API keys loaded:"
python -c "import os; print('OpenRouter:', 'YES' if os.environ.get('OPENROUTER_API_KEY') else 'NO')"

echo "✓ S3 access:"
aws s3 ls s3://devvyn.aafc-srdc.herbarium/ --region ca-central-1 | head -3

echo "✓ Last extraction:"
ls -lt deliverables/ | head -3

echo "=== All systems operational ==="
```

---

## Getting Help

### Before Filing Issue

1. **Check logs**:
   ```bash
   tail -100 extraction.log
   tail -100 ~/.cache/herbarium-extraction/debug.log
   ```

2. **Run diagnostic**:
   ```bash
   uv run python scripts/diagnose.py --full-report
   ```

3. **Document error**:
   - Exact error message
   - Command that caused it
   - System info (`uname -a`, `python --version`)

### GitHub Issues

**Template**:
```markdown
## Problem
[Brief description]

## Steps to Reproduce
1. Run command: `uv run python ...`
2. Observe error: [paste error]

## Environment
- OS: macOS 14.0 (or Linux, Windows)
- Python: 3.11.5
- Branch: main (commit: abc1234)

## Logs
[Attach relevant logs]
```

---

**Last Updated**: 2025-10-24
**Maintainer**: AAFC Herbarium Digitization Project
**Related Docs**: [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md), [REVIEW_QUICK_START.md](REVIEW_QUICK_START.md)
