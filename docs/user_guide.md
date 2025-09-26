# User Guide - Herbarium Specimen Digitization

**Step-by-step guide for institutional staff to digitize herbarium specimens using OCR automation.**

---

## Quick Reference

### Basic Workflow
1. **Setup** → Install software and organize photos
2. **Process** → Automated OCR extraction (2-4 hours for 1000 specimens)
3. **Review** → Quality control using web interface
4. **Export** → Generate Darwin Core data for GBIF/databases

### Common Commands
```bash
# Process specimens
python cli.py process --input photos/ --output results/ --engine vision

# Review results
python review_web.py --db results/candidates.db --images photos/

# Generate reports
python cli.py stats --db results/app.db --format html
```

---

## Getting Started

### First Time Setup

#### 1. Install Software
```bash
# Clone and install (one-time setup)
git clone https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025.git
cd aafc-herbarium-dwc-extraction-2025
./bootstrap.sh
```

#### 2. Organize Your Photos
Create a consistent directory structure:
```bash
mkdir -p ~/herbarium_work/batch_1/{input,output}
```

Copy your specimen photos to the input directory:
```bash
cp /path/to/your/photos/*.jpg ~/herbarium_work/batch_1/input/
```

#### 3. Verify System Ready
```bash
# Check OCR engines available
python cli.py check-deps --engines vision,tesseract,gpt

# Expected on macOS: ✅ Apple Vision: Available
```

---

## Processing Specimens

### Standard Processing Workflow

#### Step 1: Start Processing
```bash
python cli.py process \
  --input ~/herbarium_work/batch_1/input \
  --output ~/herbarium_work/batch_1/output \
  --engine vision
```

**What happens:**
- Each photo is analyzed using Apple Vision OCR
- Text is extracted and identified (scientific names, collectors, dates)
- Results are saved with confidence scores
- Progress is shown: "Processing specimen 1/100: photo_001.jpg"

#### Step 2: Monitor Progress
```bash
# Check processing status
python cli.py stats --db ~/herbarium_work/batch_1/output/app.db

# See confidence distribution
python cli.py stats --db ~/herbarium_work/batch_1/output/app.db --show-confidence
```

#### Step 3: Handle Interruptions
If processing stops, resume where it left off:
```bash
python cli.py resume \
  --input ~/herbarium_work/batch_1/input \
  --output ~/herbarium_work/batch_1/output
```

---

## Understanding Results

### Confidence Scores

#### Interpretation Guide
- **0.95-1.0**: Excellent - minimal review needed
- **0.85-0.94**: Good - spot check recommended
- **0.70-0.84**: Fair - review recommended
- **Below 0.70**: Poor - manual review required

#### Quality Expectations
Based on OCR research:
- **Apple Vision**: 95% of specimens achieve 0.85+ confidence
- **Manual review needed**: ~5% of specimens
- **High accuracy fields**: Institution names, collector names
- **Lower accuracy fields**: Handwritten notes, damaged labels

### Data Fields Extracted

#### Primary Fields (High Accuracy)
- **scientificName**: Taxonomic identification
- **collector**: Person who collected specimen
- **eventDate**: Collection date
- **locality**: Collection location
- **catalogNumber**: Institution specimen number

---

## Quality Control & Review

### Web-Based Review (Recommended)

#### Launch Review Interface
```bash
python review_web.py \
  --db ~/herbarium_work/batch_1/output/candidates.db \
  --images ~/herbarium_work/batch_1/input \
  --port 8080
```

Open browser to: http://localhost:8080

#### Review Features
- **Side-by-side view**: Photo and extracted text
- **Confidence filtering**: Focus on specimens needing attention
- **Bulk editing**: Fix common patterns across specimens
- **Quick approval**: One-click for high-confidence results

#### Focus on Problem Cases
```bash
# Review only low-confidence specimens
python review_web.py \
  --db ~/herbarium_work/batch_1/output/candidates.db \
  --images ~/herbarium_work/batch_1/input \
  --filter "confidence < 0.8"
```

---

## Data Export & Integration

### Generate Final Dataset

#### Darwin Core Export (GBIF Ready)
```bash
python cli.py archive \
  --output ~/herbarium_work/batch_1/output \
  --version 1.0.0 \
  --filter "confidence > 0.7" \
  --include-multimedia
```

**Creates**: `dwca_v1.0.0.zip` ready for GBIF submission

#### CSV Exports
Your processed data is automatically available:
- **`output/occurrence.csv`** - Darwin Core records
- **`output/identification_history.csv`** - Taxonomic determinations
- **`output/raw.jsonl`** - Complete processing logs

---

## Troubleshooting

### Processing Issues

#### "No OCR engines available"
```bash
# Check what's installed
python cli.py check-deps --engines vision,tesseract,gpt

# On macOS: Ensure Apple Vision available
# On Linux/Windows: Install Tesseract
pip install pytesseract
```

#### Processing stops with errors
```bash
# Check disk space
df -h

# Resume processing
python cli.py resume --input photos/ --output results/
```

#### Poor OCR results
1. **Check image quality**: Clear, well-lit photos work best
2. **Try different engines**: `--engine gpt` for difficult specimens
3. **Adjust confidence threshold**: `--filter "confidence > 0.6"`

### Review Interface Issues

#### Web interface won't start
```bash
# Try different port
python review_web.py --db results/candidates.db --images photos/ --port 8081

# Check database path
ls -la results/candidates.db
```

---

## Best Practices

### Photo Preparation

#### Optimal Image Quality
- **Resolution**: 2-5 megapixels sufficient
- **Format**: JPG or PNG
- **Lighting**: Even lighting, avoid shadows
- **Focus**: Ensure labels are in sharp focus
- **Angle**: Straight-on view of labels

### Quality Control

#### Review Priorities
1. **Start with low confidence**: Focus effort where needed
2. **Verify scientific names**: Use taxonomic databases
3. **Check geographic data**: Validate locality information
4. **Confirm dates**: Ensure reasonable collection dates

---

## Getting Help

### Documentation Resources
- **[FAQ](faq.md)**: Common questions and answers
- **[Troubleshooting](troubleshooting.md)**: Detailed problem solving
- **[Production Handover](PRODUCTION_HANDOVER.md)**: Complete deployment guide

### Support Channels
- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: Search docs first
- **Community**: Share experiences with other users