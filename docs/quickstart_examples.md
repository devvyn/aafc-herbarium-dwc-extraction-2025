# Quick Start Examples

**Copy-paste ready commands for common tasks**

This guide provides simple examples for the most common operations you'll perform right after installation. For detailed institutional workflows, see [workflow_examples.md](workflow_examples.md).

---

## Prerequisites

Ensure you've run the bootstrap script:
```bash
./bootstrap.sh
```

---

## 1. Process Your First Specimen

### Single Image (macOS with Apple Vision)
```bash
# Process one specimen image
python cli.py process \
  --input sample_photos/specimen_001.jpg \
  --output my_first_extraction/

# View the results
ls my_first_extraction/
# Expected files:
#   raw.jsonl           - Raw extraction results
#   occurrence.csv      - Darwin Core formatted data
#   extraction_log.txt  - Processing details
```

### Single Image (Windows/Linux with Cloud API)
```bash
# Set your API key first (one-time setup)
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# Process with GPT-4o-mini
python cli.py process \
  --engine gpt4o-mini \
  --input sample_photos/specimen_001.jpg \
  --output my_first_extraction/
```

**What you'll see**:
```
Processing specimen_001.jpg...
✓ OCR completed (confidence: 0.92)
✓ Darwin Core fields extracted (12/16 fields)
✓ Results saved to my_first_extraction/

Summary:
  Scientific name: Bouteloua gracilis (HBK.) Lag.
  Collector: J. Looman
  Date: 1969-08-14
  Locality: Beaver River crossing, Saskatchewan, Canada
```

---

## 2. Process a Small Batch

### Folder of Images (10-50 specimens)
```bash
# Process all images in a directory
python cli.py process \
  --input my_photos/ \
  --output batch_results/

# With progress display
python cli.py process \
  --input my_photos/ \
  --output batch_results/ \
  --progress
```

**Output**:
```
Processing 25 specimens...
[####################] 25/25 (100%)

Completed in 2 minutes 15 seconds
  Successful: 23 specimens
  Low confidence: 2 specimens (flagged for review)
  Failed: 0 specimens

Results saved to batch_results/occurrence.csv
```

### Process with Specific Engine
```bash
# macOS: Use Apple Vision (FREE)
python cli.py process \
  --engine vision \
  --input my_photos/ \
  --output batch_results/

# Windows: Use Azure Computer Vision
python cli.py process \
  --engine azure \
  --input my_photos/ \
  --output batch_results/

# High accuracy: Use GPT-4o-mini
python cli.py process \
  --engine gpt4o-mini \
  --input my_photos/ \
  --output batch_results/
```

---

## 3. Review and Correct Results

### Launch Web Review Interface
```bash
# Start the review web app
python cli.py review \
  --extraction-dir batch_results/ \
  --port 5002

# Then open in your browser:
# http://127.0.0.1:5002
```

**What you can do in the review interface**:
- View specimen images alongside extracted data
- Edit incorrect fields
- Approve or reject specimens
- Flag specimens for further review
- Add notes and corrections

### Review Low-Confidence Specimens Only
```bash
# Review only specimens needing attention
python cli.py review \
  --extraction-dir batch_results/ \
  --filter "confidence < 0.8" \
  --port 5002
```

### Export Corrected Data
After making corrections in the review interface, export the updated data:
```bash
# Export reviewed and approved specimens
python cli.py export \
  --extraction-dir batch_results/ \
  --filter "review_status = approved" \
  --output final_data/occurrence.csv
```

---

## 4. Export Darwin Core Archive

### Basic Export (GBIF-ready)
```bash
# Create Darwin Core Archive for GBIF submission
python cli.py export \
  --extraction-dir batch_results/ \
  --output gbif_archive/ \
  --version 1.0

# Output: gbif_archive/dwc-archive-v1.0.zip
```

**What's included in the archive**:
- `occurrence.txt` - Darwin Core occurrence records
- `meta.xml` - Archive metadata
- `eml.xml` - Dataset metadata (if configured)

### Export with Filters
```bash
# Export only high-confidence records
python cli.py export \
  --extraction-dir batch_results/ \
  --filter "confidence >= 0.85" \
  --output high_confidence_archive/ \
  --version 1.0

# Export only approved records
python cli.py export \
  --extraction-dir batch_results/ \
  --filter "review_status = approved" \
  --output approved_archive/ \
  --version 1.0
```

---

## 5. Resume Interrupted Processing

### If Processing Was Interrupted
```bash
# Resume from last checkpoint
python cli.py resume \
  --extraction-dir batch_results/

# The system will:
# - Skip already processed images
# - Continue from where it left off
# - Preserve existing results
```

---

## 6. Check Available OCR Engines

### Verify Your Setup
```bash
# Check which OCR engines are available
python cli.py check-deps

# Expected output on macOS:
# ✓ Apple Vision: Available (FREE)
# ✓ Tesseract: Available (FREE)
# ✗ GPT-4o-mini: Not configured (set OPENAI_API_KEY)
# ✗ Azure Vision: Not configured (set AZURE_COMPUTER_VISION_SUBSCRIPTION_KEY)
```

### Test an Engine
```bash
# Test GPT-4o-mini with a sample image
python cli.py check-deps --test gpt4o-mini --sample test_image.jpg
```

---

## 7. Common Processing Patterns

### Pattern 1: Free Processing (macOS)
```bash
# Use only free engines
python cli.py process \
  --engine vision \
  --input photos/ \
  --output results/

# Cost: $0
# Accuracy: 95%
# Best for: macOS users, zero-budget projects
```

### Pattern 2: Budget Processing (Windows/Linux)
```bash
# Use cheapest cloud API
python cli.py process \
  --engine azure \
  --input photos/ \
  --output results/

# Cost: $1.00 per 1,000 specimens
# Accuracy: 85%
# Best for: Large batches, tight budgets
```

### Pattern 3: High Accuracy
```bash
# Use premium AI model
python cli.py process \
  --engine gpt4o-mini \
  --input photos/ \
  --output results/

# Cost: $1.60 per 1,000 specimens
# Accuracy: 95%
# Best for: Publication-quality data
```

### Pattern 4: Cascade Strategy (Recommended)
```bash
# Use cheap engine first, escalate if needed
python cli.py process \
  --engines azure,gpt4o-mini \
  --fallback-threshold 0.85 \
  --input photos/ \
  --output results/

# Cost: ~$1.10 per 1,000 specimens (85% Azure @ $1.00, 15% GPT @ $1.60)
# Accuracy: 90%
# Best for: Production workflows
```

---

## 8. View Processing Statistics

### Check Results Summary
```bash
# View statistics for processed batch
python cli.py stats --extraction-dir batch_results/

# Output:
# Total specimens: 25
# Successfully extracted: 23 (92%)
# Low confidence: 2 (8%)
# Failed: 0 (0%)
#
# Field coverage:
#   catalogNumber: 25/25 (100%)
#   scientificName: 23/25 (92%)
#   eventDate: 20/25 (80%)
#   recordedBy: 18/25 (72%)
#   locality: 22/25 (88%)
#   ...
```

---

## 9. Real-World Example Workflows

### Workflow A: Student Research Project (50 specimens)
```bash
# 1. Process images (FREE on macOS)
python cli.py process \
  --engine vision \
  --input research_photos/ \
  --output research_results/

# 2. Review results
python cli.py review \
  --extraction-dir research_results/ \
  --port 5002

# 3. Export corrected data
python cli.py export \
  --extraction-dir research_results/ \
  --output final_data.csv

# Total time: ~30 minutes
# Cost: $0
```

### Workflow B: Museum Collection (500 specimens)
```bash
# 1. Process with cascade strategy
python cli.py process \
  --engines azure,gpt4o-mini \
  --fallback-threshold 0.85 \
  --input museum_photos/ \
  --output museum_results/ \
  --parallel 4

# 2. Review low-confidence specimens
python cli.py review \
  --extraction-dir museum_results/ \
  --filter "confidence < 0.85" \
  --port 5002

# 3. Export GBIF archive
python cli.py export \
  --extraction-dir museum_results/ \
  --filter "review_status = approved OR confidence >= 0.85" \
  --output gbif_archive/ \
  --version 1.0

# Total time: ~2 hours
# Cost: ~$0.55 (assuming 85% Azure, 15% GPT)
```

### Workflow C: Herbarium Pilot (10 specimens)
```bash
# Test different engines to see which works best
mkdir -p pilot_test/{vision,azure,gpt}

# Try Apple Vision (macOS only)
python cli.py process \
  --engine vision \
  --input pilot_photos/ \
  --output pilot_test/vision/

# Try Azure
python cli.py process \
  --engine azure \
  --input pilot_photos/ \
  --output pilot_test/azure/

# Try GPT-4o-mini
python cli.py process \
  --engine gpt4o-mini \
  --input pilot_photos/ \
  --output pilot_test/gpt/

# Compare results and choose your preferred engine
# Then process full collection with chosen engine
```

---

## 10. Troubleshooting Quick Fixes

### "Engine not available" error
```bash
# Check what's missing
python cli.py check-deps

# Install missing dependencies
uv sync --dev
```

### "API key not found" error
```bash
# Add your API key to .env file
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# Verify it's working
python cli.py check-deps --test gpt4o-mini
```

### Low accuracy results
```bash
# Try a better engine
python cli.py process \
  --engine gpt4o-mini \
  --input photos/ \
  --output better_results/

# Or improve image quality first
python scripts/enhance_images.py \
  --input photos/ \
  --output enhanced_photos/
```

### Processing too slow
```bash
# Use parallel processing
python cli.py process \
  --input photos/ \
  --output results/ \
  --parallel 4  # Use 4 CPU cores
```

---

## Next Steps

Once you're comfortable with these basic operations:

1. **Read the [OCR Engine Guide](ocr_engines.md)** to understand which engine is best for your needs
2. **Explore [Workflow Examples](workflow_examples.md)** for detailed institutional scenarios
3. **Configure [Advanced Settings](configuration.md)** to optimize for your collection
4. **Set up [Cloud APIs](CLOUD_API_SETUP.md)** for production processing

---

## Quick Reference Card

```bash
# Basic processing
python cli.py process --input photos/ --output results/

# Review results
python cli.py review --extraction-dir results/ --port 5002

# Export Darwin Core
python cli.py export --extraction-dir results/ --output archive/ --version 1.0

# Check available engines
python cli.py check-deps

# Resume interrupted processing
python cli.py resume --extraction-dir results/

# View statistics
python cli.py stats --extraction-dir results/
```

**Questions?** See [troubleshooting.md](troubleshooting.md) or [open an issue](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues).
