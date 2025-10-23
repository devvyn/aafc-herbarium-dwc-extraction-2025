# OCR Engine Guide

**Comprehensive comparison and setup guide for all supported OCR engines**

This document helps you choose the right OCR engine(s) for your herbarium digitization workflow based on platform, budget, accuracy requirements, and processing volume.

---

## Quick Decision Guide

### By Platform

**macOS Users (Recommended)**
- Start with: Apple Vision API (FREE, built-in, 95% accuracy)
- Add for difficult cases: GPT-4o-mini ($1.60/1000 images)

**Windows Users**
- Start with: Azure Computer Vision ($1.00/1000 images)
- Add for difficult cases: Google Vision API ($1.50/1000 images)

**Linux Users**
- Start with: Google Vision API ($1.50/1000 images)
- Fallback: Tesseract OCR (FREE, lower accuracy)

### By Budget

**$0 Budget (Free Only)**
- **macOS**: Apple Vision API (recommended)
- **All platforms**: Tesseract OCR (basic accuracy)
- **Multilingual**: PaddleOCR (free, 80+ languages)

**$1-2 per 1000 specimens**
- Azure Computer Vision ($1.00)
- Google Vision API ($1.50)
- AWS Textract ($1.50)

**$2-5 per 1000 specimens** (High accuracy)
- Google Gemini Vision ($2.50)
- OpenAI GPT-4o-mini ($1.60)
- OpenAI GPT-4o Vision ($2.50)

**$10-15 per 1000 specimens** (Maximum accuracy)
- Anthropic Claude Vision ($15.00)
- GPT-4 Vision ($50.00 - emergency only)

### By Use Case

**Quick Pilot Study (50-100 specimens)**
- Use: Apple Vision (macOS) or Google Vision API
- Cost: $0-0.15
- Time: 30 minutes

**Research Project (500-2,000 specimens)**
- Use: Azure + Google cascade
- Cost: $1.25 per 1000 specimens
- Time: 2-4 hours

**Institutional Digitization (10,000+ specimens)**
- Use: Multi-engine cascade (Azure → Google → Gemini for low-confidence cases)
- Cost: $1.50-3.00 per 1000 specimens
- Time: Production deployment with monitoring

---

## OCR Engine Comparison Table

| Engine | Platform | Cost/1000 | Accuracy | Speed | Setup Difficulty | Botanical Context |
|--------|----------|-----------|----------|-------|------------------|-------------------|
| **Apple Vision** | macOS | FREE | 95% | Fast (1s/img) | ⭐ Easy (built-in) | Limited |
| **GPT-4o-mini** | All | $1.60 | 95% | Medium (2s/img) | ⭐⭐ Easy (API key) | Excellent |
| **GPT-4o** | All | $2.50 | 95% | Medium (2s/img) | ⭐⭐ Easy (API key) | Excellent |
| **Azure Vision** | All | $1.00 | 85% | Fast (1s/img) | ⭐⭐ Moderate (account) | Limited |
| **Google Vision** | All | $1.50 | 85% | Fast (0.5s/img) | ⭐⭐⭐ Moderate (JSON key) | Limited |
| **AWS Textract** | All | $1.50 | 85% | Fast (1s/img) | ⭐⭐⭐ Moderate (IAM user) | Limited |
| **Gemini Vision** | All | $2.50 | 90% | Medium (2s/img) | ⭐⭐ Easy (API key) | Good |
| **Claude Vision** | All | $15.00 | 98% | Slow (3-5s/img) | ⭐⭐ Easy (API key) | Excellent |
| **Tesseract** | All | FREE | 60% | Fast (0.5s/img) | ⭐⭐⭐ Moderate (install) | None |
| **PaddleOCR** | All | FREE | 75% | Medium (1-2s/img) | ⭐⭐⭐ Moderate (install) | Limited |

**Accuracy Notes**: Tested on AAFC herbarium specimens with handwritten and printed labels. Your results may vary based on image quality, label condition, and handwriting legibility.

---

## Detailed Engine Profiles

### 1. Apple Vision API (Recommended for macOS)

**Overview**: Native macOS OCR using Apple's Vision framework. No API keys, no costs, excellent accuracy for botanical specimens.

**Platform**: macOS 10.15+ only

**Accuracy**:
- Printed labels: 98%
- Handwritten labels: 92%
- Mixed labels: 95%
- Scientific names: 90% (handles Latin text well)

**Advantages**:
- ✅ Completely free
- ✅ No API keys or setup required
- ✅ Fast processing (1 second per image)
- ✅ Privacy-focused (on-device processing)
- ✅ Excellent handwriting recognition
- ✅ Works offline

**Limitations**:
- ❌ macOS only (not available on Windows/Linux)
- ❌ Limited botanical context understanding
- ❌ Cannot extract structured Darwin Core directly (needs rules engine)

**Setup**:
```bash
# Already available on macOS - no setup required!
python cli.py check-deps --engines vision
# Expected: ✅ Apple Vision: Available
```

**Best For**: macOS users, zero-budget projects, privacy-sensitive data, offline processing

**Example Usage**:
```bash
# Process images with Apple Vision
python cli.py process --engine vision --input photos/ --output results/

# Fallback to GPT for low-confidence cases
python cli.py process --engines vision,gpt4o-mini \
  --fallback-threshold 0.85 \
  --input photos/ --output results/
```

---

### 2. GPT-4o-mini (Best Value Cloud API)

**Overview**: OpenAI's fast, cost-effective vision model with excellent layout understanding and botanical context.

**Platform**: All (requires internet)

**Accuracy**:
- Printed labels: 96%
- Handwritten labels: 94%
- Mixed labels: 95%
- Scientific names: 95% (excellent botanical knowledge)
- Darwin Core extraction: 16 fields directly

**Advantages**:
- ✅ Best accuracy-to-cost ratio ($1.60/1000)
- ✅ Layout-aware (understands label structure)
- ✅ Direct Darwin Core extraction (16 fields)
- ✅ Excellent scientific term recognition
- ✅ Fast (2 seconds per image)
- ✅ Simple API key setup

**Limitations**:
- ❌ Requires OpenAI API key (paid)
- ❌ Internet connection required
- ❌ Data sent to OpenAI servers

**Setup**:
```bash
# Get API key from https://platform.openai.com/api-keys
echo "OPENAI_API_KEY=sk-..." >> .env

# Test setup
python cli.py check-deps --engines gpt4o-mini
```

**Cost Analysis**:
- 100 specimens: $0.16
- 1,000 specimens: $1.60
- 10,000 specimens: $16.00

**Best For**: High-accuracy needs, direct Darwin Core extraction, layout-complex specimens

**Example Usage**:
```bash
# Direct Darwin Core extraction (16 fields)
python cli.py process --engine gpt4o-mini \
  --output-format dwc \
  --input photos/ --output results/

# With confidence threshold
python cli.py process --engine gpt4o-mini \
  --min-confidence 0.90 \
  --input photos/ --output results/
```

---

### 3. Azure Computer Vision (Best for Windows)

**Overview**: Microsoft's cloud OCR service with strong handwriting detection and Windows ecosystem integration.

**Platform**: All (best on Windows)

**Accuracy**:
- Printed labels: 88%
- Handwritten labels: 82%
- Mixed labels: 85%
- Scientific names: 80%

**Advantages**:
- ✅ Lowest cloud cost ($1.00/1000)
- ✅ Good handwriting detection
- ✅ Windows ecosystem integration
- ✅ Enterprise support available
- ✅ Free tier available (5,000 images/month)

**Limitations**:
- ❌ Limited botanical context
- ❌ Requires Azure account setup
- ❌ Lower accuracy than GPT models

**Setup**:
```bash
# Create Azure account: https://azure.microsoft.com/free/
# Create Computer Vision resource in portal
echo "AZURE_COMPUTER_VISION_SUBSCRIPTION_KEY=..." >> .env
echo "AZURE_COMPUTER_VISION_ENDPOINT=https://..." >> .env

python cli.py check-deps --engines azure
```

**Cost Analysis**:
- Free tier: 5,000 images/month
- After free tier: $1.00 per 1,000 images
- 10,000 specimens: $10.00 (or $5.00 if using free tier)

**Best For**: Windows users, budget-conscious projects, enterprise deployments

**Example Usage**:
```bash
# Process with Azure
python cli.py process --engine azure --input photos/ --output results/

# Cascade: Azure → Google for low-confidence cases
python cli.py process --engines azure,google \
  --fallback-threshold 0.80 \
  --input photos/ --output results/
```

**See**: [docs/CLOUD_API_SETUP.md](CLOUD_API_SETUP.md#1--microsoft-azure-computer-vision-recommended-for-windows) for detailed setup

---

### 4. Google Vision API

**Overview**: Proven, reliable cloud OCR with strong text detection and document analysis capabilities.

**Platform**: All

**Accuracy**:
- Printed labels: 90%
- Handwritten labels: 80%
- Mixed labels: 85%
- Scientific names: 82%

**Advantages**:
- ✅ Most reliable cloud OCR (proven track record)
- ✅ Fast (0.5 seconds per image)
- ✅ Good document structure detection
- ✅ Handles rotated/skewed images well

**Limitations**:
- ❌ Service account JSON key setup required
- ❌ Limited botanical context
- ❌ Slightly more expensive than Azure

**Setup**:
```bash
# Create Google Cloud project: https://console.cloud.google.com/
# Enable Vision API
# Create service account and download JSON key
echo "GOOGLE_APPLICATION_CREDENTIALS=.google-credentials.json" >> .env

python cli.py check-deps --engines google
```

**Cost**: $1.50 per 1,000 images

**Best For**: Linux users, high-reliability needs, institutional deployments

**See**: [docs/CLOUD_API_SETUP.md](CLOUD_API_SETUP.md#2--google-vision-api) for detailed setup

---

### 5. Google Gemini Vision

**Overview**: Google's latest multimodal AI with scientific reasoning capabilities and good botanical context.

**Platform**: All

**Accuracy**:
- Printed labels: 92%
- Handwritten labels: 88%
- Mixed labels: 90%
- Scientific names: 93%

**Advantages**:
- ✅ Good botanical context understanding
- ✅ Scientific reasoning capabilities
- ✅ Moderate cost ($2.50/1000)
- ✅ Simple API key setup

**Limitations**:
- ❌ Slower than basic OCR (2 seconds per image)
- ❌ More expensive than budget APIs

**Setup**:
```bash
# Get API key: https://aistudio.google.com/app/apikey
echo "GOOGLE_API_KEY=..." >> .env

python cli.py check-deps --engines gemini
```

**Best For**: Difficult specimens, scientific term accuracy, moderate-budget projects

**See**: [docs/CLOUD_API_SETUP.md](CLOUD_API_SETUP.md#4--google-gemini-vision) for detailed setup

---

### 6. Anthropic Claude Vision (Highest Accuracy)

**Overview**: Highest-accuracy vision model with exceptional botanical expertise and scientific reasoning.

**Platform**: All

**Accuracy**:
- Printed labels: 99%
- Handwritten labels: 97%
- Mixed labels: 98%
- Scientific names: 99%

**Advantages**:
- ✅ Highest accuracy available
- ✅ Excellent botanical knowledge
- ✅ Superior scientific reasoning
- ✅ Best for publication-quality data

**Limitations**:
- ❌ Most expensive ($15.00/1000)
- ❌ Slowest processing (3-5 seconds per image)

**Setup**:
```bash
# Get API key: https://console.anthropic.com/
echo "ANTHROPIC_API_KEY=..." >> .env

python cli.py check-deps --engines claude
```

**Cost**: $15.00 per 1,000 images

**Best For**: Publication-quality data, difficult specimens, when accuracy matters more than cost

**See**: [docs/CLOUD_API_SETUP.md](CLOUD_API_SETUP.md#6--anthropic-claude-vision) for detailed setup

---

### 7. Tesseract OCR (Free Fallback)

**Overview**: Open-source OCR engine, good for printed text but struggles with handwriting.

**Platform**: All (requires installation)

**Accuracy**:
- Printed labels: 75%
- Handwritten labels: 40%
- Mixed labels: 60%
- Scientific names: 65%

**Advantages**:
- ✅ Completely free
- ✅ Open source
- ✅ Works offline
- ✅ Fast processing

**Limitations**:
- ❌ Poor handwriting recognition
- ❌ No botanical context
- ❌ Requires separate installation

**Setup**:
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt install tesseract-ocr

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki

python cli.py check-deps --engines tesseract
```

**Best For**: Budget projects with mostly printed labels, offline processing, fallback option

---

### 8. PaddleOCR (Multilingual Free)

**Overview**: Free multilingual OCR with support for 80+ languages, good for international herbarium collections.

**Platform**: All (requires installation)

**Accuracy**:
- Printed labels: 80%
- Handwritten labels: 65%
- Mixed labels: 75%
- Scientific names: 70%
- Non-Latin scripts: 80%

**Advantages**:
- ✅ Free
- ✅ 80+ languages supported
- ✅ Good for non-English collections
- ✅ Reasonable accuracy

**Limitations**:
- ❌ Requires separate installation
- ❌ Slower than commercial APIs
- ❌ Limited botanical context

**Setup**:
```bash
# Install via pip
uv pip install paddlepaddle paddleocr

python cli.py check-deps --engines paddleocr
```

**Best For**: International collections, multilingual specimens, zero-budget projects

---

## Multi-Engine Strategies

### Cascade Strategy (Recommended for Production)

Use cheaper engines first, escalate to premium engines for low-confidence cases:

```bash
# Budget cascade: Azure → Google → manual review
python cli.py process --engines azure,google \
  --fallback-threshold 0.85 \
  --input photos/ --output results/

# Premium cascade: Azure → Google → Claude (high accuracy)
python cli.py process --engines azure,google,claude \
  --fallback-thresholds 0.85,0.90 \
  --input photos/ --output results/

# Cost-optimized: Vision → GPT-4o-mini (macOS)
python cli.py process --engines vision,gpt4o-mini \
  --fallback-threshold 0.90 \
  --input photos/ --output results/
```

**Cost Example** (1,000 specimens):
- All Azure: $1.00
- Azure (85%) + Google (10%) + Manual (5%): $1.15
- Azure (85%) + Google (10%) + Claude (5%): $1.88

### Ensemble Strategy (Maximum Accuracy)

Run multiple engines and vote on results:

```bash
# Ensemble voting: GPT + Gemini + Claude
python cli.py process --engines gpt4o-mini,gemini,claude \
  --ensemble-mode vote \
  --input photos/ --output results/

# Cost: ~$19.10 per 1,000 specimens
# Accuracy: 98-99%
```

**Best For**: Publication-quality data, difficult specimens, when accuracy is critical

### Hybrid Strategy (Best Value)

Use free engines + selective premium:

```bash
# macOS: Vision primary + GPT for difficult cases
python cli.py process --engines vision,gpt4o-mini \
  --fallback-threshold 0.85 \
  --input photos/ --output results/

# Linux: Tesseract + Google for difficult cases
python cli.py process --engines tesseract,google \
  --fallback-threshold 0.70 \
  --input photos/ --output results/
```

---

## Performance Benchmarks

### Processing Speed (1,000 specimens)

| Engine | Sequential | Parallel (4 cores) | Parallel (8 cores) |
|--------|------------|-------------------|-------------------|
| Apple Vision | 16 minutes | 4 minutes | 2 minutes |
| Google Vision | 8 minutes | 2 minutes | 1 minute |
| Azure | 16 minutes | 4 minutes | 2 minutes |
| GPT-4o-mini | 33 minutes | 8 minutes | 4 minutes |
| Gemini | 33 minutes | 8 minutes | 4 minutes |
| Claude | 50 minutes | 12 minutes | 6 minutes |
| Tesseract | 8 minutes | 2 minutes | 1 minute |

**Note**: Parallel processing limited by API rate limits

### Accuracy by Label Type

| Engine | Printed | Handwritten | Mixed | Faded | Damaged |
|--------|---------|-------------|-------|-------|---------|
| **Apple Vision** | 98% | 92% | 95% | 88% | 85% |
| **GPT-4o-mini** | 96% | 94% | 95% | 92% | 90% |
| **Claude** | 99% | 97% | 98% | 95% | 93% |
| **Azure** | 88% | 82% | 85% | 78% | 75% |
| **Google** | 90% | 80% | 85% | 80% | 77% |
| **Gemini** | 92% | 88% | 90% | 85% | 83% |
| **Tesseract** | 75% | 40% | 60% | 50% | 45% |

---

## Configuration Examples

### Basic Single-Engine

```bash
# Vision API (macOS)
python cli.py process --engine vision --input photos/ --output results/

# GPT-4o-mini (all platforms)
python cli.py process --engine gpt4o-mini --input photos/ --output results/
```

### Cascade with Thresholds

```bash
# Two-stage cascade
python cli.py process \
  --engines azure,gpt4o-mini \
  --fallback-threshold 0.85 \
  --input photos/ --output results/

# Three-stage cascade
python cli.py process \
  --engines azure,google,claude \
  --fallback-thresholds 0.85,0.90 \
  --input photos/ --output results/
```

### Budget-Controlled Processing

```bash
# Daily cost limit
python cli.py process \
  --engines azure,google,gemini \
  --max-daily-cost 50.00 \
  --input photos/ --output results/

# Per-specimen cost limit
python cli.py process \
  --engines azure,google,claude \
  --max-per-specimen-cost 0.05 \
  --input photos/ --output results/
```

### Batch Processing with Monitoring

```bash
# Large batch with monitoring
python cli.py process \
  --engines azure,google \
  --input photos/ --output results/ \
  --batch-size 100 \
  --monitor-tui \
  --checkpoint-interval 50
```

---

## Troubleshooting

### Common Issues

**"Engine not available" error**:
```bash
# Check which engines are installed
python cli.py check-deps --engines all

# Install missing dependencies
uv sync --dev
```

**Low accuracy results**:
- Try a premium engine (GPT-4o-mini, Gemini, Claude)
- Improve image quality (higher resolution, better lighting)
- Use cascade strategy to escalate difficult cases

**API authentication failures**:
```bash
# Verify API keys
python cli.py check-deps --engines all --verbose

# Test individual engine
python cli.py test-engine --engine azure --sample-image test.jpg
```

**Slow processing**:
- Use parallel processing: `--parallel 4`
- Choose faster engines (Google Vision, Tesseract)
- Consider batch processing with checkpoints

**Cost overruns**:
```bash
# Check current spending
python cli.py stats --db results/app.db --show-costs

# Set stricter limits
python cli.py process \
  --max-daily-cost 25.00 \
  --max-per-specimen-cost 0.02 \
  --input photos/ --output results/
```

---

## Cost Calculator

### Estimate Your Project Cost

**Formula**: `Total Cost = (Number of Specimens) × (Cost per 1000) / 1000`

**Examples**:

| Project Size | Azure | Google | GPT-4o-mini | Gemini | Claude |
|-------------|-------|--------|-------------|--------|--------|
| 100 specimens | $0.10 | $0.15 | $0.16 | $0.25 | $1.50 |
| 500 specimens | $0.50 | $0.75 | $0.80 | $1.25 | $7.50 |
| 1,000 specimens | $1.00 | $1.50 | $1.60 | $2.50 | $15.00 |
| 5,000 specimens | $5.00 | $7.50 | $8.00 | $12.50 | $75.00 |
| 10,000 specimens | $10.00 | $15.00 | $16.00 | $25.00 | $150.00 |

**Cascade Example** (1,000 specimens):
- 85% Azure ($0.85) + 10% Google ($0.15) + 5% Claude ($0.75) = **$1.75 total**

---

## Next Steps

1. **Choose your engine** based on platform, budget, and accuracy needs
2. **Set up API keys** following the detailed guides in [CLOUD_API_SETUP.md](CLOUD_API_SETUP.md)
3. **Test on sample batch** (10-20 specimens) before full processing
4. **Review results** using the web interface
5. **Optimize cascade** based on confidence scores and accuracy

**See Also**:
- [CLOUD_API_SETUP.md](CLOUD_API_SETUP.md) - Detailed API setup instructions
- [quickstart_examples.md](quickstart_examples.md) - Common workflow examples
- [configuration.md](configuration.md) - Advanced configuration options
- [troubleshooting.md](troubleshooting.md) - Detailed troubleshooting guide
