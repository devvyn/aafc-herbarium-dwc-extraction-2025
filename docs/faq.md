# Frequently Asked Questions (FAQ)

Common questions and answers about the herbarium OCR to Darwin Core toolkit.

## General Questions

### What is this toolkit for?

The herbarium OCR to Darwin Core toolkit is designed for digitizing herbarium specimen collections. It processes images of pressed plant specimens, extracts text information using OCR (Optical Character Recognition), and maps the results to the Darwin Core biodiversity data standard for publication and sharing.

### What makes this different from other OCR tools?

This toolkit is specifically designed for herbarium specimens and includes:
- Multiple OCR engines optimized for handwritten scientific labels
- Built-in Darwin Core field mapping
- GBIF taxonomic validation
- Quality control workflows for scientific data
- Support for multilingual historical specimens
- Export formats compatible with biodiversity databases

### Who should use this toolkit?

- Herbarium managers and curators
- Biodiversity data managers
- Research institutions digitizing natural history collections
- GBIF data publishers
- Botanical researchers working with specimen data

## Installation and Setup

### What operating systems are supported?

The toolkit works on:
- **macOS**: Full support including Apple Vision framework
- **Linux**: Full support with all open-source engines
- **Windows**: Supported via WSL (Windows Subsystem for Linux)

### Do I need programming experience?

Basic command-line familiarity is helpful, but not extensive programming knowledge. The toolkit provides:
- Simple command-line interface
- Web-based review interface
- Configuration files instead of code changes
- Comprehensive documentation and examples

### What OCR engines are supported?

- **Tesseract**: Free, open-source, good for typed text
- **Apple Vision**: macOS only, excellent for handwritten text
- **PaddleOCR**: Free, supports 80+ languages
- **GPT-4 Vision**: Commercial API, best overall accuracy but requires OpenAI subscription

### How much does it cost to run?

- **Free options**: Tesseract, Apple Vision (macOS), PaddleOCR
- **Commercial**: GPT-4 Vision typically costs $0.01-0.05 per image depending on size and API pricing

For a collection of 1,000 specimens using GPT-4 Vision, expect costs of $10-50.

## Data and Processing

### What image formats are supported?

- **Supported**: JPG, PNG, TIFF, BMP
- **Recommended**: High-resolution JPG (300+ DPI)
- **File naming**: Use consistent naming like `INSTITUTION_BARCODE.jpg`

### What image quality do I need?

**Minimum requirements**:
- Resolution: 150 DPI or higher
- Readable text when viewed at 100% zoom
- Good contrast between text and background

**Recommended**:
- Resolution: 300+ DPI
- Well-lit, even lighting
- Specimen label clearly visible
- Minimal glare or shadows

### How accurate is the OCR?

Accuracy depends on several factors:

**Text Type**:
- Typed labels: 90-98% accuracy
- Clear handwriting: 80-95% accuracy
- Poor handwriting: 60-85% accuracy
- Historical faded labels: 40-80% accuracy

**OCR Engine**:
- GPT-4 Vision: Best overall, especially for handwriting
- Apple Vision: Excellent for handwriting on macOS
- Tesseract: Good for typed text, improving with v5
- PaddleOCR: Good multilingual support

### How long does processing take?

Processing time per specimen:
- **Tesseract**: 1-5 seconds
- **Apple Vision**: 2-8 seconds
- **PaddleOCR**: 3-10 seconds
- **GPT-4 Vision**: 10-30 seconds (including API latency)

For 1,000 specimens:
- Tesseract only: 30 minutes - 2 hours
- Multiple engines: 2-8 hours
- GPT-4 Vision included: 4-12 hours

### Can I process specimens in multiple languages?

Yes! The toolkit supports multilingual processing:

**Supported languages** (depending on engine):
- Latin script: English, French, German, Spanish, Italian, etc.
- Extended Latin: Danish, Swedish, Polish, Czech, etc.
- Cyrillic: Russian, Ukrainian, Bulgarian
- Asian languages: Chinese, Japanese (with PaddleOCR)

**Configuration example**:
```toml
[ocr]
langs = ["en", "fr", "de", "la"]  # English, French, German, Latin
preferred_engine = "paddleocr"

[paddleocr]
lang = "latin"
```

## Darwin Core and Data Standards

### What is Darwin Core?

Darwin Core is the global standard for biodiversity data. It defines fields like:
- `scientificName`: Taxonomic name
- `decimalLatitude/decimalLongitude`: Geographic coordinates
- `eventDate`: Collection date
- `recordedBy`: Collector name
- `basisOfRecord`: Type of specimen record

### What Darwin Core fields are extracted?

The toolkit extracts common specimen fields:

**Taxonomic**:
- Scientific name, family, genus, species
- Identification history and determiners

**Geographic**:
- Country, state/province, locality
- Coordinates (if present on label)

**Temporal**:
- Collection date, identification date

**People**:
- Collector names, determiner names

**Administrative**:
- Institution codes, catalog numbers

### How do I customize field mapping?

Edit the mapping configuration:

```toml
[dwc.mappings]
# Map OCR text patterns to Darwin Core fields
collector = ["collected by", "leg.", "coll."]
locality = ["locality", "loc.", "site"]
coordinates = ["lat", "long", "°N", "°W"]
```

### Is the output compatible with GBIF?

Yes! The toolkit:
- Follows Darwin Core standard structure
- Validates taxonomic names against GBIF backbone
- Exports Darwin Core Archive (DwC-A) format
- Includes required GBIF metadata fields

## Quality Control and Review

### How do I ensure data quality?

The toolkit provides multiple quality control layers:

**Automated**:
- Confidence scoring for OCR results
- GBIF taxonomic validation
- Geographic coordinate validation
- Duplicate detection

**Manual**:
- Web-based review interface
- Flagging of low-confidence records
- Batch editing capabilities
- Expert review workflows

### What confidence scores should I use?

**Recommended thresholds**:
- **High confidence**: >0.8 - minimal review needed
- **Medium confidence**: 0.5-0.8 - spot check recommended
- **Low confidence**: <0.5 - manual review required

**Configuration**:
```toml
[ocr]
confidence_threshold = 0.7  # Minimum for auto-acceptance

[qc]
manual_review_threshold = 0.5  # Flag for review below this
```

### How do I handle problematic specimens?

**Common issues and solutions**:

1. **Faded labels**: Use contrast enhancement preprocessing
2. **Handwritten text**: Enable GPT or Apple Vision engines
3. **Multiple languages**: Configure language detection
4. **Damaged labels**: Manual data entry may be required
5. **Ambiguous text**: Flag for expert review

**Reprocessing workflow**:
```bash
# Identify problematic specimens
python qc/identify_problems.py --db ./output/app.db

# Reprocess with enhanced settings
python cli.py process \
  --input ./problematic \
  --config config/enhanced.toml \
  --engine gpt
```

## Export and Publishing

### What export formats are available?

**Standard formats**:
- **CSV**: For spreadsheet analysis
- **Darwin Core Archive (DwC-A)**: For GBIF publishing
- **JSONL**: For programmatic processing
- **Excel**: For manual review and editing

**Custom exports**:
```bash
# Export specific fields
python export_review.py \
  --format csv \
  --fields "scientificName,decimalLatitude,decimalLongitude" \
  --output coordinates.csv

# Export with filters
python export_review.py \
  --format dwca \
  --filter "confidence > 0.8" \
  --version 2.0.0
```

### How do I publish to GBIF?

1. **Prepare data**:
```bash
python cli.py archive \
  --output ./output/collection \
  --version 1.0.0 \
  --gbif-validate
```

2. **Validate compliance**:
```bash
python qc/gbif_compliance.py \
  --input ./output/collection/dwca_v1.0.0.zip
```

3. **Upload to IPT** (Integrated Publishing Toolkit)
4. **Register dataset with GBIF**

### Can I integrate with existing collection management systems?

Yes, through various approaches:

**Data import/export**:
- CSV import to Specify, Symbiota, etc.
- API integration with modern systems
- Custom field mapping for institutional schemas

**Database integration**:
```python
# Example: Export to institutional database
python export_review.py \
  --format sql \
  --schema institutional \
  --output import_statements.sql
```

## Troubleshooting

### The OCR results are poor. What can I improve?

**Check image quality**:
```bash
python scripts/analyze_image_quality.py --input ./problematic/
```

**Try preprocessing adjustments**:
```toml
[preprocess]
pipeline = ["grayscale", "contrast", "deskew", "binarize"]
contrast_factor = 1.5
binarize_method = "adaptive"
```

**Use multiple engines**:
```bash
python cli.py process \
  --engine tesseract \
  --engine vision \
  --engine gpt \
  --confidence-threshold 0.6
```

### Processing is very slow. How can I speed it up?

**Optimize for speed**:
```toml
[preprocess]
max_dim_px = 1500  # Smaller images
pipeline = ["resize", "grayscale"]  # Minimal preprocessing

[ocr]
preferred_engine = "tesseract"  # Fastest engine
enabled_engines = ["tesseract"]  # Single engine
```

**Parallel processing**:
```bash
# Process in batches
python scripts/parallel_process.py \
  --input ./large_collection \
  --workers 4 \
  --batch-size 100
```

### I'm getting API errors with GPT-4 Vision

**Common solutions**:

1. **Rate limiting**:
```toml
[gpt]
rate_limit_delay = 2.0  # Seconds between requests
batch_size = 5
```

2. **API key issues**:
```bash
# Verify API key
echo $OPENAI_API_KEY
python -c "import openai; print(openai.OpenAI().models.list())"
```

3. **Network connectivity**:
```bash
# Test connection
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

### Where can I get help?

1. **Documentation**: Check the docs/ directory
2. **GitHub Issues**: Report bugs and request features
3. **Configuration Examples**: See config/ directory
4. **Community**: Join discussions in GitHub Discussions

**Creating a support request**:
```bash
# Generate diagnostic bundle
python scripts/create_support_bundle.py \
  --output support_bundle.zip \
  --include-config \
  --include-logs
```

Include this bundle when requesting help to provide context about your setup and any errors encountered.