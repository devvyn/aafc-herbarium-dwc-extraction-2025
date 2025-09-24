# User Guide: Herbarium Digitization Workflows

This guide provides step-by-step instructions for common herbarium digitization scenarios using the OCR to Darwin Core toolkit.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Complete Institutional Workflow](#complete-institutional-workflow)
3. [Small Collection Processing](#small-collection-processing)
4. [Multi-language Specimens](#multi-language-specimens)
5. [Quality Control Procedures](#quality-control-procedures)
6. [Export and Data Publishing](#export-and-data-publishing)

## Quick Start

### Prerequisites

- Python 3.11 or later
- API keys for GPT models (optional but recommended)
- Collection of herbarium specimen images (JPG/PNG format)

### Installation and Setup

```bash
# Clone and set up the environment
git clone <repository-url>
cd aafc-herbarium-dwc-extraction-2025
./bootstrap.sh

# Configure API keys
cp .env.example .env
# Edit .env to add your OPENAI_API_KEY
```

### Processing Your First Specimen

```bash
# Create input directory and add images
mkdir -p ./input/test-specimens
# Copy your specimen images to ./input/test-specimens/

# Process with multiple OCR engines
python cli.py process \
  --input ./input/test-specimens \
  --output ./output/test-run \
  --engine tesseract \
  --engine vision \
  --engine gpt

# Review results
ls ./output/test-run/
# occurrence.csv - Darwin Core records
# raw.jsonl - Detailed OCR results
# candidates.db - Raw OCR data
```

## Complete Institutional Workflow

This workflow is designed for institutions processing hundreds to thousands of specimens.

### Step 1: Preparation and Planning

```bash
# Create organized directory structure
mkdir -p ./input/collection-2024
mkdir -p ./output/collection-2024
mkdir -p ./backup/collection-2024

# Verify specimen images are properly named
# Recommended format: INSTITUTION_BARCODE.jpg
# Example: AAFC_12345678.jpg
ls ./input/collection-2024/ | head -10
```

### Step 2: Configuration Setup

Create a custom configuration file for your institution:

```bash
cp config/config.default.toml config/institution.toml
```

Edit `config/institution.toml`:

```toml
[ocr]
preferred_engine = "gpt"
enabled_engines = ["gpt", "tesseract", "vision"]
confidence_threshold = 0.7

[gpt]
model = "gpt-4-vision-preview"
dry_run = false
fallback_threshold = 0.5

[dwc]
assume_country_if_missing = "Canada"  # Adjust for your institution
strict_minimal_fields = true

[preprocess]
pipeline = ["grayscale", "deskew", "binarize", "resize"]
max_dim_px = 3000
```

### Step 3: Batch Processing

```bash
# Start initial processing
python cli.py process \
  --input ./input/collection-2024 \
  --output ./output/collection-2024 \
  --config config/institution.toml \
  --engine gpt \
  --engine tesseract

# Monitor progress
tail -f ./output/collection-2024/app.log

# Resume if interrupted
python cli.py resume \
  --input ./input/collection-2024 \
  --output ./output/collection-2024 \
  --config config/institution.toml
```

### Step 4: Quality Control Review

```bash
# Launch web-based review interface
python review_web.py \
  --db ./output/collection-2024/candidates.db \
  --images ./input/collection-2024 \
  --port 8080

# Open browser to http://localhost:8080
# Review and validate OCR results
# Mark specimens for reprocessing if needed
```

### Step 5: Export and Publishing

```bash
# Create versioned export
python cli.py archive \
  --output ./output/collection-2024 \
  --version 1.0.0 \
  --filter "confidence > 0.7"

# Result: ./output/collection-2024/dwca_v1.0.0.zip
# Contains: occurrence.csv, meta.xml, manifest.json
```

## Small Collection Processing

For collections under 100 specimens, use this streamlined approach:

### Single Command Processing

```bash
# Process with default settings
python cli.py process \
  --input ./input/small-collection \
  --output ./output/small-collection \
  --engine tesseract \
  --engine gpt

# Quick review using TUI
python review.py ./output/small-collection/candidates.db specimen_001.jpg --tui
```

### Immediate Export

```bash
# Export without versioning for quick analysis
python export_review.py \
  --db ./output/small-collection/app.db \
  --format csv \
  --output ./output/small-collection/results.csv
```

## Multi-language Specimens

For collections with non-English labels (common in historical collections):

### Configuration for Multiple Languages

```toml
[ocr]
langs = ["en", "fr", "de", "la"]  # English, French, German, Latin
preferred_engine = "paddleocr"    # Best for multilingual text

[paddleocr]
lang = "latin"  # Use Latin character set
```

### Processing Command

```bash
python cli.py process \
  --input ./input/multilingual \
  --output ./output/multilingual \
  --config config/multilingual.toml \
  --engine paddleocr \
  --engine gpt
```

### Language-Specific Review

```bash
# Review with language context
python review_web.py \
  --db ./output/multilingual/candidates.db \
  --images ./input/multilingual \
  --language-filter "fr,de,la"
```

## Quality Control Procedures

### Automated Quality Checks

```bash
# Run GBIF validation
python qc/gbif.py \
  --input ./output/collection-2024/occurrence.csv \
  --output ./output/collection-2024/gbif_validation.json

# Check for duplicates
python qc/duplicates.py \
  --db ./output/collection-2024/app.db \
  --threshold 0.95
```

### Manual Review Guidelines

1. **High Priority Review**: Specimens with confidence < 0.7
2. **Taxonomic Validation**: Scientific names not found in GBIF
3. **Geographic Validation**: Coordinates outside expected ranges
4. **Date Validation**: Collection dates in the future or before 1800

### Review Workflow

```bash
# Export specimens needing review
python export_review.py \
  --db ./output/collection-2024/app.db \
  --filter "confidence < 0.7 OR gbif_match = false" \
  --format xlsx \
  --output ./review/needs_attention.xlsx

# After review, import corrections
python import_review.py \
  --db ./output/collection-2024/app.db \
  --input ./review/corrected_data.xlsx
```

## Export and Data Publishing

### Darwin Core Archive Creation

```bash
# Create standards-compliant DwC-A
python cli.py archive \
  --output ./output/collection-2024 \
  --version 2.0.0 \
  --include-multimedia \
  --gbif-validate
```

### Custom Export Formats

```bash
# CSV for analysis
python export_review.py \
  --db ./output/collection-2024/app.db \
  --format csv \
  --fields "scientificName,decimalLatitude,decimalLongitude,eventDate" \
  --output ./exports/coordinates.csv

# JSONL for processing
python export_review.py \
  --db ./output/collection-2024/app.db \
  --format jsonl \
  --output ./exports/full_records.jsonl
```

### Data Validation Before Publishing

```bash
# Comprehensive validation
python qc/validate_export.py \
  --input ./output/collection-2024/dwca_v2.0.0.zip \
  --output ./validation/report.html

# Check required Darwin Core fields
python qc/dwc_compliance.py \
  --input ./output/collection-2024/occurrence.csv \
  --standard "occurrence"
```

## Troubleshooting Common Issues

### Low OCR Confidence

```bash
# Reprocess with preprocessing
python cli.py process \
  --input ./problematic/images \
  --output ./reprocessed \
  --config config/high_quality.toml \
  --engine gpt \
  --preprocess-pipeline "grayscale,contrast,deskew,binarize"
```

### Missing Geographic Data

```bash
# Use locality lookup
python qc/locality_enrichment.py \
  --db ./output/collection-2024/app.db \
  --gazetteer "geonames" \
  --update
```

### API Rate Limiting

```toml
[gpt]
rate_limit_delay = 2.0  # seconds between requests
batch_size = 10         # process in smaller batches
```

For more specific troubleshooting, see [Troubleshooting Guide](troubleshooting.md).