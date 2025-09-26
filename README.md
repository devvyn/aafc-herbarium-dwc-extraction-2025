# Herbarium OCR to Darwin Core

Convert your herbarium specimen photos into structured scientific data.

## Quick Start: Digitize Your Specimens in 3 Steps

Got specimen photos? Get Darwin Core data in 3 simple steps:

```bash
# 1. Install (one time setup)
./bootstrap.sh

# 2. Process your photos (automated OCR extraction)
python cli.py process --input photos/ --output results/

# 3. Review and export data (quality control)
python review_web.py --db results/candidates.db --images photos/
```

**Your data is now ready** in `results/occurrence.csv` for GBIF, institutional databases, or research.

---

## What This Tool Does

**Converts specimen photos → structured botanical data**

- **Extracts text** from specimen labels using advanced OCR
- **Identifies key information**: scientific names, collectors, dates, locations
- **Follows international standards**: Darwin Core format for biodiversity databases
- **Provides quality control**: review interface to verify and correct results
- **Exports clean data**: ready for GBIF, museum databases, or research projects

### Example: Photo → Data

**From this**: Herbarium specimen photo with handwritten/printed labels
**To this**: Structured database record

```csv
scientificName,collector,eventDate,locality,catalogNumber
"Plantago major","Smith, J.R.","2023-07-15","Ontario, Canada","HERB-001234"
```

---

## Is This Right For My Workflow?

**✅ YES - Use this tool if you have:**
- Herbarium specimen photographs
- Need to extract text data from labels
- Want Darwin Core formatted output
- Need data for GBIF, institutional databases, or research

**❌ NO - This tool is not for:**
- Live plant identification (try iNaturalist)
- Non-herbarium specimen types
- Photos without text labels
- Real-time field identification

---

## Installation

### System Requirements
- **macOS, Linux, or Windows**
- **Python 3.11+** ([download here](https://www.python.org/downloads/))
- **Recommended**: macOS for best OCR accuracy (95% with Apple Vision)

### Quick Install
```bash
# Clone the project
git clone https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025.git
cd aafc-herbarium-dwc-extraction-2025

# Run setup script (installs everything)
./bootstrap.sh
```

### Manual Install (if needed)
```bash
# Install dependencies
uv sync --dev

# Copy environment file
cp .env.example .env

# Test installation
uv run pytest -q
```

---

## Basic Workflow

### Step 1: Prepare Your Images
- **Format**: JPG or PNG files
- **Organization**: Put all photos in one folder
- **Naming**: Any filename works (metadata preserved)

```bash
photos/
├── specimen_001.jpg
├── specimen_002.jpg
└── specimen_003.jpg
```

### Step 2: Process Photos (Automated)
```bash
# Basic processing with recommended settings
python cli.py process --input photos/ --output results/

# With specific OCR engine (Apple Vision recommended)
python cli.py process --input photos/ --output results/ --engine vision
```

**What happens**: The tool automatically reads each image, extracts text, and identifies botanical information.

### Step 3: Review Results
```bash
# Launch web interface for easy review
python review_web.py --db results/candidates.db --images photos/
```

**Opens in browser**: Side-by-side view of photos and extracted data for verification.

### Step 4: Export Final Data
Your processed data is automatically saved:
- **`results/occurrence.csv`** - Darwin Core records (ready for GBIF)
- **`results/raw.jsonl`** - Complete processing log with confidence scores
- **`results/manifest.json`** - Processing metadata and settings

---

## OCR Engine Performance

**Apple Vision is recommended** based on comprehensive testing with real herbarium specimens:

| Engine | Accuracy | Cost | Best For |
|--------|----------|------|----------|
| **Apple Vision** | **95%** | **Free** | **Primary choice (macOS)** |
| Claude Vision | 98%* | $15/1000 | Difficult specimens |
| GPT-4 Vision | 95%* | $50/1000 | High accuracy needs |
| Tesseract | 15% | Free | Not recommended |

*Requires API key setup

**Why Apple Vision?**
- Highest accuracy for herbarium labels
- No API costs or usage limits
- Handles mixed fonts and handwriting
- Built into macOS (no additional setup)

---

## Review Your Results

### Web Interface (Recommended)
```bash
python review_web.py --db results/candidates.db --images photos/
```

**Features:**
- Visual comparison of photos and extracted text
- One-click corrections and approvals
- Bulk editing for common patterns
- Confidence-based filtering

### Quick Quality Check
```bash
# Generate processing statistics
python cli.py stats --db results/app.db --format html

# View confidence distribution
python cli.py stats --db results/app.db --show-confidence
```

### Export for Institution Review
```bash
# Create Excel file for curatorial review
python export_review.py --db results/app.db --format xlsx --output review.xlsx

# Import corrections back
python import_review.py --db results/app.db --input reviewed.xlsx
```

---

## Common Workflows

### Process New Batch
```bash
python cli.py process --input new_photos/ --output batch_2/
```

### Resume Interrupted Processing
```bash
python cli.py resume --input photos/ --output results/
```

### Merge Multiple Batches
```bash
python cli.py merge --inputs batch_1/ batch_2/ batch_3/ --output combined/
```

### Create Archive for Publication
```bash
python cli.py archive --output results/ --version 1.0.0 --include-multimedia
```

---

## Troubleshooting

### Common Issues

**"No OCR engines available"**
```bash
# Check what's installed
python cli.py check-deps --engines vision,tesseract,gpt

# Install missing dependencies
pip install pytesseract  # for Tesseract
```

**Poor OCR results**
- Try Apple Vision on macOS (95% accuracy)
- Check image quality (clear, well-lit photos work best)
- Use confidence filtering: `--filter "confidence > 0.7"`

**Review interface won't start**
```bash
# Check database path
python review_web.py --db results/candidates.db --images photos/ --port 8080
```

### Getting Help
- **Detailed guides**: See [`docs/`](docs/) folder
- **Configuration**: [`docs/configuration.md`](docs/configuration.md)
- **API setup**: [`docs/gpt.md`](docs/gpt.md)
- **Issues**: [GitHub Issues](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues)

---

## Advanced Usage

### Custom Configuration
```bash
# Use custom settings
python cli.py process --config my_config.toml --input photos/ --output results/
```

### API Integration (GPT-4, Claude)
```bash
# Add API key to .env file
echo "OPENAI_API_KEY=your-key-here" >> .env

# Process with GPT-4 Vision
python cli.py process --engine gpt --input photos/ --output results/
```

### Quality Control Workflows
```bash
# Generate QC report
python qc/comprehensive_qc.py --db results/app.db --output qc_report.html

# GBIF taxonomy validation
python cli.py validate-taxonomy --db results/app.db
```

---

## Technical Details

<details>
<summary>Click to expand technical information</summary>

### Output Files
| File | Purpose | Format |
|------|---------|---------|
| `occurrence.csv` | Darwin Core records | CSV |
| `identification_history.csv` | Taxonomic determinations | CSV |
| `raw.jsonl` | Complete processing log | JSONL |
| `candidates.db` | OCR results for review | SQLite |
| `app.db` | Processing status | SQLite |

### Dependencies
- Python 3.11+
- uv or pip for package management
- Optional: Tesseract, OpenAI API, Claude API

### Configuration
- Main config: `config/config.default.toml`
- Custom mappings: `config/rules/`
- Prompts: `config/prompts/`

### Development
```bash
# Run tests
pytest

# Lint code
ruff check . --fix

# Development setup
./bootstrap.sh
```

</details>

---

## Current Version: 0.3.0

**Major OCR research breakthrough** - Apple Vision validated as optimal herbarium digitization engine (95% accuracy vs 15% for Tesseract). Production-ready processing pipeline with comprehensive testing infrastructure.

See [CHANGELOG.md](CHANGELOG.md) for version history and [docs/roadmap.md](docs/roadmap.md) for upcoming features.

---

## Contributing

We welcome contributions! See:
- [Development Guide](docs/development.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Issue Templates](.github/ISSUE_TEMPLATE/)

For questions or support, please [open an issue](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues).