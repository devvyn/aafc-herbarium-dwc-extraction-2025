# Herbarium OCR to Darwin Core

Extract text data from herbarium specimen photos and convert to Darwin Core format.

## Quick Start

```bash
# Install
./bootstrap.sh

# Process photos
python cli.py process --input photos/ --output results/
```

Successful processing creates `results/occurrence.csv` with your data.

## What This Does

Reads text from specimen labels and creates structured data files.

- Reads handwritten and printed labels using OCR
- Extracts scientific names, dates, locations, collector names
- Outputs Darwin Core format (standard for biodiversity data)
- Provides review interface to check and correct results

### Example

**Input**: Herbarium specimen photo with handwritten/printed labels
**Output**: Structured database record

```csv
scientificName,collector,eventDate,locality,catalogNumber
"Plantago major","Smith, J.R.","2023-07-15","Ontario, Canada","HERB-001234"
```

## When To Use This

**Use this if you have:**
- Photos of herbarium specimens with text labels
- Need data for GBIF or institutional databases

**Don't use this for:**
- Live plant identification (try iNaturalist instead)
- Specimens without readable labels

---

## Installation

### Requirements
- macOS, Linux, or Windows
- Python 3.11+ ([download](https://www.python.org/downloads/))
- Note: Best results observed on macOS with Apple Vision OCR

### Setup

```bash
git clone https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025.git
cd aafc-herbarium-dwc-extraction-2025
./bootstrap.sh
```

#### macOS
Apple Vision OCR works out of the box. No API keys needed.

```bash
python cli.py check-deps --engines vision
# Expected: ✅ Apple Vision: Available
```

#### Windows/Linux
Add API keys for cloud OCR services:

```bash
cp .env.example .env
# Edit .env and add your API keys for:
# - AZURE_COMPUTER_VISION_SUBSCRIPTION_KEY
# - GOOGLE_APPLICATION_CREDENTIALS
# - OPENAI_API_KEY (optional)
```

---

## Basic Workflow

### 1. Prepare Images
Put specimen photos in a folder:

```bash
photos/
├── specimen_001.jpg
├── specimen_002.jpg
└── specimen_003.jpg
```

### 2. Process Photos

```bash
python cli.py process --input photos/ --output results/
```

The tool reads each image, extracts text, and identifies botanical information.

### 3. Review Results

```bash
python review_web.py --db results/candidates.db --images photos/
```

Opens browser with side-by-side view for verification.

### 4. Use Your Data

Output files:
- `results/occurrence.csv` - Darwin Core records (ready for GBIF)
- `results/raw.jsonl` - Processing log with confidence scores
- `results/manifest.json` - Processing metadata

---

## OCR Accuracy

Based on informal testing with herbarium specimens:

**macOS**: Apple Vision produces clean, readable text
**Windows/Linux**: Cloud OCR services available (quality varies by service)

**All OCR results should be manually reviewed before database submission.**

### Available OCR Engines

**macOS (built-in)**
- Apple Vision: free, works well on herbarium labels in our tests

**Cloud services (all platforms)**
- Azure Vision: $1/1000 images
- Google Vision: $1.50/1000 images
- Google Gemini: $2.50/1000 images
- GPT-4o Vision: $2.50/1000 images
- Claude Vision: $15/1000 images

Processing typically costs $0-5 per 1,000 specimens depending on platform and engine choice.

---

## User Interfaces

**Web interface** (recommended for review):
```bash
python review_web.py --db results/candidates.db --images photos/
```

**Terminal interface**:
```bash
python herbarium_ui.py --tui
```

**Command line** (for scripts):
```bash
python cli.py process --input photos/ --output results/
```

**Quick trial** (5 sample images):
```bash
python herbarium_ui.py --trial
```

---

## Common Tasks

**Resume interrupted processing**:
```bash
python cli.py resume --input photos/ --output results/
```

**Check processing statistics**:
```bash
python cli.py stats --db results/app.db
```

**Export for curator review**:
```bash
python export_review.py --db results/app.db --format xlsx --output review.xlsx
```

**Process with specific OCR engine**:
```bash
python cli.py process --input photos/ --output results/ --engine vision
```

---

## Current Limitations

- OCR accuracy depends on label quality and handwriting clarity
- All extracted data should be manually reviewed before use
- Processing time: approximately 3-4 hours for 2,800 specimens
- Active development: tool is functional but under ongoing improvement
- Accuracy claims based on informal testing, not rigorous validation

---

## Troubleshooting

**"No OCR engines available"**

macOS:
```bash
python cli.py check-deps --engines vision
```

Windows/Linux:
```bash
# Check .env file has API keys
python cli.py check-deps --engines google,azure
```

**Poor OCR results**
- Check image quality (clear, well-lit photos work best)
- Try different OCR engines if available
- Use confidence filtering: `--filter "confidence > 0.8"`

**Review interface won't start**
```bash
python review_web.py --db results/candidates.db --images photos/ --port 8080
```

---

## Documentation

- Configuration: [docs/configuration.md](docs/configuration.md)
- API setup: [docs/gpt.md](docs/gpt.md)
- Development: [docs/development.md](docs/development.md)
- Full guide: [docs/user_guide.md](docs/user_guide.md)

---

## Technical Details

<details>
<summary>Click to expand</summary>

### Output Files
| File | Purpose |
|------|---------|
| `occurrence.csv` | Darwin Core records |
| `identification_history.csv` | Taxonomic determinations |
| `raw.jsonl` | Processing log |
| `candidates.db` | OCR results for review |
| `app.db` | Processing status |

### Configuration
- Main config: `config/config.default.toml`
- Custom mappings: `config/rules/`
- Prompts: `config/prompts/`

### Development
```bash
pytest                    # Run tests
ruff check . --fix        # Lint code
```

</details>

---

## Version

Current: 0.3.0

See [CHANGELOG.md](CHANGELOG.md) for version history and [docs/roadmap.md](docs/roadmap.md) for planned features.

---

## Contributing

See [Development Guide](docs/development.md) for contribution guidelines.

For questions or issues: [GitHub Issues](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues)
