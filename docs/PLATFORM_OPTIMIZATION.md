# Platform Optimization Guide

**Choose the optimal OCR configuration based on your operating system and hardware.**

---

## Platform Decision Tree

### ✅ **macOS Users (Recommended)**
**Use Apple Vision** - 95% accuracy, $0 cost, optimal performance

```bash
# Use default configuration (Apple Vision primary)
python cli.py process --input photos/ --output results/
```

### 🪟 **Windows 11 Users**
**Use Cloud APIs** - 90-98% accuracy, managed costs, hardware-independent

```bash
# Use Windows-optimized configuration
python cli.py process --input photos/ --output results/ --config config/config.windows.toml
```

### 🐧 **Linux Users**
**Use Cloud APIs** - Same as Windows, with Linux paths

---

## Platform-Specific Configurations

### **Apple Vision (macOS Only)**

#### **Advantages**
- ✅ **95% accuracy** on herbarium specimens
- ✅ **$0 cost** - no API fees
- ✅ **Privacy** - no data leaves your machine
- ✅ **Speed** - 1.7 seconds per image
- ✅ **No dependencies** - built into macOS

#### **Setup**
```bash
# Automatic - no configuration needed
python cli.py check-deps --engines vision
# Expected: ✅ Apple Vision: Available
```

#### **Optimal Workflow**
```bash
# Process large batches efficiently
python cli.py process --input photos/ --output results/ --engine vision

# For 2,800 specimens: ~4 hours, $0 cost
```

### **Cloud APIs (Windows/Linux)**

#### **Cost-Effective Strategy**
| API | Primary Use | Cost/1000 | Accuracy |
|-----|-------------|-----------|----------|
| **Google Vision** | **Primary** | **$1.50** | **85%** |
| Claude Vision | Difficult cases | $15 | 98% |
| GPT-4 Vision | Final fallback | $50 | 95% |

#### **Windows 11 Setup**

1. **Install with Windows configuration**:
```bash
# Clone project
git clone https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025.git
cd aafc-herbarium-dwc-extraction-2025

# Install dependencies
./bootstrap.sh

# Use Windows-optimized config
cp config/config.windows.toml config/config.local.toml
```

2. **Set up Google Vision (Primary)**:
```bash
# Install Google Cloud SDK
# Download service account JSON from Google Cloud Console
# Save as .google-credentials.json in project root
```

3. **Add API keys for fallback**:
```bash
# Add to .env file
echo "GOOGLE_APPLICATION_CREDENTIALS=.google-credentials.json" >> .env
echo "OPENAI_API_KEY=your-openai-key-here" >> .env
echo "ANTHROPIC_API_KEY=your-claude-key-here" >> .env
```

#### **Processing with Cost Control**
```bash
# Process with budget limits
python cli.py process --input photos/ --output results/ \
  --config config/config.windows.toml \
  --max-cost 50

# Monitor costs during processing
python cli.py stats --db results/app.db --show-costs
```

#### **Old Hardware Optimization**
```bash
# Process in smaller batches for old systems
python cli.py process --input photos/ --output results/ \
  --config config/config.windows.toml \
  --batch-size 25 \
  --max-concurrent 1
```

---

## Research Assistant Guidelines

### **Windows 11 + Old Hardware Strategy**

#### **Cost-Conscious Workflow**
1. **Start with Google Vision** (~$1.50/1000 specimens)
2. **Flag low confidence** for manual review (< 75%)
3. **Use premium APIs** only for critical specimens
4. **Process in small batches** (25-50 specimens)

#### **Budget Planning**
```bash
# Cost estimates for different batch sizes
# 100 specimens with Google Vision primary:
#   - 85 high confidence: $0.128 (Google only)
#   - 15 low confidence: $0.225 (Google) + manual review
#   - Total: ~$0.35 per 100 specimens

# 1000 specimens estimated cost: $3.50 with Google primary
# vs $1600 savings compared to manual transcription
```

#### **Quality Assurance**
```bash
# Review workflow for Windows users
python review_web.py --db results/candidates.db --images photos/ \
  --filter "confidence < 0.80 OR api_cost > 0.02"

# Focus manual effort where it matters most
```

### **Institutional Recommendations**

#### **For Herbarium Directors**
- **macOS workstations**: Optimal ROI with Apple Vision
- **Windows research assistants**: Google Vision primary, budget $5-10/1000 specimens
- **Mixed environment**: Process locally on macOS, review on any platform

#### **For Research Assistants**
- **Daily budget**: $10-20 for 500-1000 specimens
- **Weekly planning**: Process 2000-5000 specimens per week
- **Quality focus**: Manual review saves money vs premium APIs

---

## Migration from Tesseract

### **Why Retire Tesseract?**
Based on comprehensive research:
- **Tesseract accuracy**: 15% on herbarium specimens
- **With preprocessing**: Maximum 42% accuracy
- **Apple Vision**: 95% accuracy
- **Google Vision**: 85% accuracy

**Conclusion**: Even free Tesseract costs more in manual correction time than Google Vision API fees.

### **Migration Steps**

1. **Update configuration**:
```bash
# Backup old config
cp config/config.default.toml config/config.backup.toml

# Remove Tesseract dependencies
pip uninstall pytesseract

# Use new platform-optimized configs
```

2. **Test new setup**:
```bash
# Test with sample images
python scripts/manage_sample_images.py create-bundle demo --output test_samples/
python cli.py process --input test_samples/demo --output test_results/ \
  --config config/config.windows.toml
```

3. **Validate results**:
```bash
# Compare accuracy with previous Tesseract results
python cli.py stats --db test_results/app.db --compare-engines
```

### **Fallback Strategy**
If cloud APIs are unavailable:
```bash
# Emergency local processing (not recommended)
python cli.py process --input photos/ --output results/ \
  --engine manual_review_only \
  --export-for-external-processing
```

---

## Performance Benchmarks

### **Processing Speed by Platform**

| Platform | Engine | Speed | Cost/1000 | Accuracy |
|----------|--------|--------|-----------|----------|
| **macOS** | Apple Vision | 500/hour | $0 | 95% |
| Windows | Google Vision | 400/hour | $1.50 | 85% |
| Windows | GPT-4 Vision | 200/hour | $50 | 95% |
| Windows | Claude Vision | 300/hour | $15 | 98% |

### **Total Cost of Ownership**

#### **1000 Specimens Processing**
```
macOS + Apple Vision:
  Processing: $0
  Manual review (5%): 2 hours @ $25/hour = $50
  Total: $50

Windows + Google Vision:
  API costs: $1.50
  Manual review (15%): 6 hours @ $25/hour = $150
  Total: $151.50

Traditional Manual (baseline):
  100% manual: 40 hours @ $25/hour = $1000
  Total: $1000
```

**ROI**: Apple Vision = 95% savings, Cloud APIs = 85% savings

---

## Troubleshooting Platform Issues

### **macOS Issues**
```bash
# Apple Vision not available
python cli.py check-deps --engines vision
# If failed: Update to macOS 11+ and Xcode command line tools

# Performance issues
# Check available memory and close other applications
```

### **Windows Issues**
```bash
# API authentication failures
python cli.py check-deps --engines google,gpt,claude
# Verify API keys in .env file and credentials.json path

# Old hardware performance
# Reduce batch size and concurrent requests in config
```

### **Universal Issues**
```bash
# Network connectivity for APIs
curl -I https://api.openai.com/v1/models
curl -I https://api.anthropic.com/v1/messages

# Disk space for processing
df -h  # Linux/macOS
dir C:\ # Windows
```

---

## Best Practices Summary

### **For Maximum Accuracy (macOS)**
- Use Apple Vision as primary
- Add Claude Vision for difficult specimens
- Manual review only for edge cases

### **For Cost-Effective Processing (Windows)**
- Start with Google Vision
- Budget $2-5 per 1000 specimens
- Focus manual effort on low-confidence results

### **For Mixed Environments**
- Process on macOS when available
- Use Windows for review and quality control
- Centralized database for institutional workflows

**Result**: Optimal accuracy and cost-effectiveness for each platform while maintaining consistent institutional workflows.