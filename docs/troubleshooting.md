# Troubleshooting Guide

This guide helps diagnose and resolve common issues when using the herbarium OCR to Darwin Core toolkit.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [OCR Engine Problems](#ocr-engine-problems)
3. [Image Processing Issues](#image-processing-issues)
4. [API and Network Issues](#api-and-network-issues)
5. [Data Quality Problems](#data-quality-problems)
6. [Performance Issues](#performance-issues)
7. [Export and Format Issues](#export-and-format-issues)

## Installation Issues

### Python Version Compatibility

**Problem**: Import errors or syntax issues
```
SyntaxError: invalid syntax
ModuleNotFoundError: No module named 'X'
```

**Solution**:
```bash
# Check Python version
python --version
# Should be 3.11 or later

# If using older Python, install newer version
# macOS with Homebrew:
brew install python@3.11

# Update pip and install
pip install --upgrade pip
pip install -e .[dev]
```

### Dependency Installation Failures

**Problem**: Installation fails with compilation errors

**Solution**:
```bash
# Clear pip cache
pip cache purge

# Install with verbose output to identify issues
pip install -e .[dev] -v

# For M1/M2 Macs with compilation issues:
export ARCHFLAGS="-arch arm64"
pip install -e .[dev]

# Alternative: use conda for problematic packages
conda install tesseract pillow
```

### Missing System Dependencies

**Problem**: `ImportError: cannot import name 'X'` for Tesseract or other engines

**macOS Solution**:
```bash
# Install Tesseract
brew install tesseract

# Install additional language packs if needed
brew install tesseract-lang

# Verify installation
tesseract --version
```

**Linux Solution**:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-fra tesseract-ocr-deu

# Verify installation
tesseract --version
```

## OCR Engine Problems

### Tesseract Not Found

**Problem**:
```
TesseractNotFoundError: tesseract is not installed
```

**Solution**:
```bash
# Check if tesseract is in PATH
which tesseract

# If not found, install and add to PATH
# Add to ~/.bashrc or ~/.zshrc:
export PATH="/opt/homebrew/bin:$PATH"  # macOS with Homebrew

# Test configuration
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

### Poor OCR Quality

**Problem**: Low confidence scores, garbled text output

**Diagnosis**:
```bash
# Check image quality
python scripts/diagnose_images.py --input ./input/problematic/

# Test with different preprocessing
python cli.py process \
  --input ./test-single-image \
  --output ./test-output \
  --config config/debug.toml \
  --engine tesseract \
  --debug
```

**Solutions**:

1. **Improve image preprocessing**:
```toml
[preprocess]
pipeline = ["grayscale", "contrast", "deskew", "binarize", "denoise"]
contrast_factor = 1.3
binarize_method = "adaptive"
```

2. **Adjust Tesseract parameters**:
```toml
[tesseract]
oem = 1  # Neural nets LSTM engine
psm = 6  # Uniform block of text
extra_args = ["--dpi", "300"]
```

3. **Use higher resolution images**:
```bash
# Resize images before processing
python scripts/resize_images.py \
  --input ./low_res_images \
  --output ./high_res_images \
  --min-dpi 300
```

### Apple Vision Framework Issues

**Problem**: Vision engine not working on macOS

**Solution**:
```bash
# Ensure you're running on macOS 10.15+
sw_vers

# Install PyObjC if missing
pip install pyobjc-framework-Vision

# Test Vision availability
python -c "import Vision; print('Vision available')"
```

### PaddleOCR Installation Issues

**Problem**: PaddleOCR fails to install or run

**Solution**:
```bash
# Clear package cache
pip cache purge

# Install with specific versions
pip install paddlepaddle==2.4.2 paddleocr==2.6.1.3

# For M1 Macs, use CPU version
pip install paddlepaddle -i https://pypi.tuna.tsinghua.edu.cn/simple/

# Test installation
python -c "from paddleocr import PaddleOCR; print('PaddleOCR ready')"
```

## Image Processing Issues

### Unsupported Image Formats

**Problem**:
```
PIL.UnidentifiedImageError: cannot identify image file
```

**Solution**:
```bash
# Convert images to supported formats
find ./input -name "*.tiff" -exec convert {} {}.jpg \;

# Check image integrity
python scripts/validate_images.py --input ./input/

# Supported formats: JPG, PNG, TIFF, BMP
```

### Large Image Memory Issues

**Problem**:
```
MemoryError: cannot allocate memory
PIL.Image.DecompressionBombError
```

**Solution**:
```toml
[preprocess]
max_dim_px = 2000  # Reduce from default 4000
pipeline = ["resize", "grayscale", "binarize"]  # Resize first
```

**Alternative**:
```bash
# Batch resize before processing
python scripts/batch_resize.py \
  --input ./huge_images \
  --output ./resized_images \
  --max-dimension 2000
```

### Preprocessing Pipeline Failures

**Problem**: Images fail during preprocessing

**Diagnosis**:
```bash
# Test individual preprocessing steps
python -c "
from preprocess.flows import preprocess_image
from pathlib import Path
result = preprocess_image(Path('problematic.jpg'), ['grayscale'])
print(f'Grayscale: {result is not None}')
"
```

**Solution**:
```toml
[preprocess]
# Start with minimal pipeline
pipeline = ["grayscale"]
# Add steps incrementally: "deskew", "binarize", "resize"
```

## API and Network Issues

### OpenAI API Errors

**Problem**:
```
openai.RateLimitError: Rate limit exceeded
openai.AuthenticationError: Invalid API key
```

**Solutions**:

1. **Rate limiting**:
```toml
[gpt]
rate_limit_delay = 2.0  # seconds between requests
max_retries = 3
batch_size = 5  # process fewer images at once
```

2. **Authentication**:
```bash
# Verify API key
echo $OPENAI_API_KEY

# Test API access
python -c "
import openai
client = openai.OpenAI()
models = client.models.list()
print('API key valid')
"
```

3. **Network connectivity**:
```bash
# Test network access
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Use proxy if needed
export https_proxy=http://proxy.company.com:8080
```

### GBIF API Timeouts

**Problem**: GBIF validation fails with timeouts

**Solution**:
```toml
[qc.gbif]
timeout = 30  # increase timeout
retry_delay = 5
max_retries = 3
batch_size = 10  # smaller batches
```

**Alternative - Offline Mode**:
```bash
# Download GBIF backbone for offline use
python scripts/download_gbif_backbone.py --output ./data/gbif/

# Configure offline validation
python qc/gbif.py --offline --backbone ./data/gbif/backbone.csv
```

## Data Quality Problems

### Missing Required Darwin Core Fields

**Problem**: Export validation fails due to missing required fields

**Diagnosis**:
```bash
# Check field coverage
python qc/field_coverage.py \
  --db ./output/collection/app.db \
  --report ./reports/field_coverage.html
```

**Solution**:
```toml
[dwc]
strict_minimal_fields = false  # Allow incomplete records
assume_country_if_missing = "Canada"  # Set default country
default_basis_of_record = "PreservedSpecimen"
```

### Invalid Coordinates

**Problem**: Geographic coordinates outside valid ranges

**Solution**:
```bash
# Run coordinate validation
python qc/coordinates.py \
  --input ./output/occurrence.csv \
  --fix-common-errors \
  --output ./output/occurrence_fixed.csv

# Common fixes applied:
# - Swap lat/long if reversed
# - Convert degrees/minutes/seconds to decimal
# - Remove leading zeros
```

### Taxonomic Name Issues

**Problem**: Scientific names not recognized by GBIF

**Diagnosis**:
```bash
# Generate taxonomic report
python qc/taxonomy_report.py \
  --db ./output/collection/app.db \
  --output ./reports/taxonomy.xlsx
```

**Solution**:
```bash
# Use fuzzy matching for similar names
python qc/gbif.py \
  --db ./output/collection/app.db \
  --fuzzy-threshold 0.8 \
  --update-names

# Manual review of unmatched names
python review_web.py \
  --db ./output/collection/candidates.db \
  --filter "gbif_match = false"
```

## Performance Issues

### Slow Processing Speed

**Problem**: Processing takes much longer than expected

**Diagnosis**:
```bash
# Profile processing time
python cli.py process \
  --input ./test-small \
  --output ./test-output \
  --profile \
  --engine tesseract

# Check bottlenecks in log
grep "processing time" ./test-output/app.log
```

**Solutions**:

1. **Optimize OCR engine selection**:
```toml
[ocr]
preferred_engine = "tesseract"  # Fastest for most cases
enabled_engines = ["tesseract"]  # Disable slower engines initially
```

2. **Reduce image size**:
```toml
[preprocess]
max_dim_px = 1500  # Smaller images process faster
pipeline = ["resize", "grayscale"]  # Minimal preprocessing
```

3. **Batch processing**:
```bash
# Process in smaller batches
python scripts/batch_process.py \
  --input ./large_collection \
  --output ./output \
  --batch-size 50 \
  --parallel 4
```

### High Memory Usage

**Problem**: Process uses excessive memory or crashes

**Solution**:
```bash
# Monitor memory usage
python cli.py process \
  --input ./test \
  --output ./output \
  --memory-limit 4GB

# Process sequentially instead of batch
python cli.py process \
  --input ./large_collection \
  --output ./output \
  --sequential
```

## Export and Format Issues

### Invalid Darwin Core Archive

**Problem**: Generated DwC-A fails validation

**Diagnosis**:
```bash
# Validate archive structure
python qc/validate_dwca.py \
  --input ./output/dwca_v1.0.0.zip \
  --output ./validation_report.html
```

**Solution**:
```bash
# Regenerate with strict validation
python cli.py archive \
  --output ./output/collection \
  --version 1.0.1 \
  --validate-strict \
  --fix-encoding
```

### CSV Export Encoding Issues

**Problem**: Special characters corrupted in CSV files

**Solution**:
```bash
# Export with UTF-8 BOM for Excel compatibility
python export_review.py \
  --db ./output/app.db \
  --format csv \
  --encoding utf-8-sig \
  --output ./exports/compatible.csv
```

### Large Export File Issues

**Problem**: Export files too large for downstream systems

**Solution**:
```bash
# Split large exports
python export_review.py \
  --db ./output/app.db \
  --format csv \
  --split-size 10000 \
  --output-prefix ./exports/batch_

# Compress exports
gzip ./exports/*.csv
```

## Getting Additional Help

### Debug Mode

Enable verbose logging for detailed diagnostics:

```bash
python cli.py process \
  --input ./problematic \
  --output ./debug-output \
  --log-level DEBUG \
  --save-intermediates
```

### Generate Support Bundle

```bash
# Create comprehensive diagnostic report
python scripts/create_support_bundle.py \
  --output ./support_bundle.zip \
  --include-logs \
  --include-config \
  --include-sample-data
```

### Community Resources

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check docs/ directory for detailed guides
- **Configuration Examples**: See config/ directory for working configurations

### Configuration Validation

```bash
# Validate your configuration before processing
python scripts/validate_config.py --config ./config/custom.toml

# Test all engines
python scripts/test_engines.py --config ./config/custom.toml
```
