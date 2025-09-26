# Cloud API Setup Guide - 7 Vision APIs

**Complete setup instructions for all supported cloud vision APIs for herbarium OCR.**

---

## 🎯 **API Overview & Strategy**

### **Cost-Optimized Cascade Strategy**
```
Budget APIs ($1-1.50/1000):     Azure → Google → AWS Textract
Premium APIs ($2.50-15/1000):  Gemini → GPT-4o → Claude
Ultra-Premium ($50/1000):      GPT-4 Vision (emergency only)
```

### **Platform Recommendations**
- **macOS**: Apple Vision (free, 95% accuracy) + premium APIs for difficult cases
- **Windows**: Azure primary + cascade fallback for comprehensive coverage
- **Linux**: Google Vision primary + multi-cloud fallback

---

## 1. 🔵 **Microsoft Azure Computer Vision** (RECOMMENDED FOR WINDOWS)

### **Why Azure First?**
- **Lowest cost**: $1.00/1000 images
- **Windows integration**: Best Microsoft ecosystem support
- **Handwriting detection**: Good for herbarium labels
- **Enterprise support**: Institutional billing available

### **Setup Steps**
1. **Create Azure Account**: https://azure.microsoft.com/en-us/free/
2. **Create Computer Vision Resource**:
   ```bash
   # Via Azure Portal
   Resource Type: Computer Vision
   Pricing Tier: F0 (Free) or S1 (Pay-as-you-go)
   Region: Choose closest to your location
   ```
3. **Get Subscription Key**:
   - Go to your Computer Vision resource
   - Copy **Key 1** and **Endpoint URL**
4. **Configure Environment**:
   ```bash
   echo "AZURE_COMPUTER_VISION_SUBSCRIPTION_KEY=your-key-here" >> .env
   echo "AZURE_COMPUTER_VISION_ENDPOINT=https://your-region.cognitiveservices.azure.com/" >> .env
   ```

### **Test Setup**
```bash
python cli.py check-deps --engines azure
# Expected: ✅ Azure Computer Vision: Available
```

---

## 2. 🟢 **Google Vision API**

### **Why Google Vision?**
- **Proven reliability**: Most tested cloud OCR
- **Good accuracy**: 85% on herbarium specimens
- **Reasonable cost**: $1.50/1000 images
- **Document detection**: Specialized for text extraction

### **Setup Steps**
1. **Create Google Cloud Project**: https://console.cloud.google.com/
2. **Enable Vision API**:
   ```bash
   # In Google Cloud Console
   APIs & Services → Library → Vision API → Enable
   ```
3. **Create Service Account**:
   ```bash
   IAM & Admin → Service Accounts → Create Service Account
   Role: Cloud Vision API User
   Download JSON key file
   ```
4. **Configure Environment**:
   ```bash
   # Save JSON file as .google-credentials.json
   echo "GOOGLE_APPLICATION_CREDENTIALS=.google-credentials.json" >> .env
   ```

### **Test Setup**
```bash
python cli.py check-deps --engines google
# Expected: ✅ Google Vision: Available
```

---

## 3. 🟠 **AWS Textract**

### **Why AWS Textract?**
- **Document analysis**: Excellent for structured forms
- **Table extraction**: Handles herbarium data sheets
- **AWS integration**: Good for existing AWS infrastructure
- **Same cost as Google**: $1.50/1000 images

### **Setup Steps**
1. **Create AWS Account**: https://aws.amazon.com/
2. **Create IAM User**:
   ```bash
   # In AWS Console
   IAM → Users → Add User
   Permissions: AmazonTextractFullAccess
   Access Type: Programmatic access
   ```
3. **Configure AWS CLI or Environment**:
   ```bash
   # Option 1: AWS CLI
   aws configure

   # Option 2: Environment variables
   echo "AWS_ACCESS_KEY_ID=your-access-key" >> .env
   echo "AWS_SECRET_ACCESS_KEY=your-secret-key" >> .env
   echo "AWS_DEFAULT_REGION=us-east-1" >> .env
   ```

### **Test Setup**
```bash
python cli.py check-deps --engines textract
# Expected: ✅ AWS Textract: Available
```

---

## 4. 🟡 **Google Gemini Vision**

### **Why Gemini?**
- **Latest AI**: Google's newest multimodal model
- **Scientific reasoning**: Good botanical context understanding
- **Moderate cost**: $2.50/1000 images
- **High accuracy**: ~90% on complex specimens

### **Setup Steps**
1. **Get Gemini API Key**: https://aistudio.google.com/app/apikey
2. **Configure Environment**:
   ```bash
   echo "GOOGLE_API_KEY=your-gemini-api-key" >> .env
   ```
3. **Enable Safety Settings** (optional):
   ```bash
   # Edit config/config.default.toml
   [gemini]
   safety_settings = "block_few"  # For scientific content
   ```

### **Test Setup**
```bash
python cli.py check-deps --engines gemini
# Expected: ✅ Google Gemini: Available
```

---

## 5. 🔴 **OpenAI GPT-4o Vision**

### **Why GPT-4o?**
- **Speed**: Faster than GPT-4 Vision
- **Cost-effective**: $2.50/1000 vs $50/1000 for GPT-4
- **High accuracy**: 95% on herbarium specimens
- **Botanical context**: Excellent understanding of scientific terms

### **Setup Steps**
1. **Create OpenAI Account**: https://platform.openai.com/
2. **Generate API Key**: https://platform.openai.com/api-keys
3. **Configure Environment**:
   ```bash
   echo "OPENAI_API_KEY=your-openai-api-key" >> .env
   ```
4. **Set Model in Config**:
   ```toml
   [gpt4o]
   model = "gpt-4o"  # Not gpt-4-vision-preview
   ```

### **Test Setup**
```bash
python cli.py check-deps --engines gpt4o
# Expected: ✅ OpenAI GPT-4o: Available
```

---

## 6. 🟣 **Anthropic Claude Vision**

### **Why Claude Vision?**
- **Highest accuracy**: 98% on herbarium specimens
- **Botanical expertise**: Excellent scientific reasoning
- **Context understanding**: Handles complex layouts
- **Premium pricing**: $15/1000 images

### **Setup Steps**
1. **Create Anthropic Account**: https://console.anthropic.com/
2. **Generate API Key**: In your dashboard
3. **Configure Environment**:
   ```bash
   echo "ANTHROPIC_API_KEY=your-claude-api-key" >> .env
   ```
4. **Enable Botanical Context**:
   ```toml
   [claude]
   botanical_context = true
   model = "claude-3-5-sonnet-20241022"
   ```

### **Test Setup**
```bash
python cli.py check-deps --engines claude
# Expected: ✅ Anthropic Claude: Available
```

---

## 7. 🔴 **OpenAI GPT-4 Vision** (EMERGENCY FALLBACK)

### **Why GPT-4 Vision Last?**
- **Ultra-premium**: $50/1000 images (20x more than Azure)
- **High accuracy**: 95% but not worth the cost premium
- **Emergency only**: Use when all other APIs fail

### **Setup Steps**
Same as GPT-4o, but:
```toml
[gpt]
model = "gpt-4-vision-preview"
fallback_threshold = 0.95  # Only for most difficult cases
```

---

## 🚀 **Quick Setup Commands**

### **Complete Windows Setup** (All APIs)
```bash
# 1. Install dependencies
uv sync

# 2. Copy Windows configuration
cp config/config.windows.toml config/config.local.toml

# 3. Add all API keys to .env
cat >> .env << EOF
AZURE_COMPUTER_VISION_SUBSCRIPTION_KEY=your-azure-key
GOOGLE_APPLICATION_CREDENTIALS=.google-credentials.json
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
GOOGLE_API_KEY=your-gemini-key
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-claude-key
EOF

# 4. Test all APIs
python cli.py check-deps --engines azure,google,textract,gemini,gpt4o,claude,gpt
```

### **Budget-Only Setup** (Minimum cost)
```bash
# Setup only budget APIs: Azure + Google
python cli.py process --engines azure,google --input photos/ --output results/
# Expected cost: ~$1-1.50 per 1000 specimens
```

### **Premium Setup** (Maximum accuracy)
```bash
# Setup premium cascade: Azure → Google → Claude
python cli.py process --engines azure,google,claude --input photos/ --output results/
# Expected cost: ~$1-15 per 1000 specimens (adaptive)
```

---

## 💰 **Cost Management**

### **Budget Controls**
```bash
# Set daily spending limits
python cli.py process --input photos/ --output results/ \
  --max-daily-cost 50 --max-weekly-cost 200
```

### **Cost Monitoring**
```bash
# Track spending by API
python cli.py stats --db results/app.db --show-api-costs

# Generate cost report
python cli.py report --db results/app.db --format cost-breakdown
```

### **Cost Optimization Tips**

1. **Start with Azure/Google** for 80-85% accuracy at $1-1.50/1000
2. **Use premium APIs selectively** for low-confidence cases only
3. **Process in batches** to manage daily spending
4. **Review confidence thresholds** to optimize API usage
5. **Manual review** often cheaper than ultra-premium APIs

### **ROI Comparison**
```
1000 Specimen Processing Costs:

Manual Transcription:     $1600 (40 hours @ $40/hour)
Azure Primary:            $1.00 + ~$200 manual review = $201 (87% savings)
Google Primary:           $1.50 + ~$150 manual review = $151.50 (91% savings)
Claude Premium:           $15.00 + ~$50 manual review = $65 (96% savings)
Mixed Strategy (optimal): $3-8 + ~$100 manual review = $103-108 (93-94% savings)
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

**API Authentication Failures**
```bash
# Check all environment variables
python cli.py check-deps --engines all --verbose

# Test individual APIs
python cli.py test-api --engine azure --sample-image test.jpg
```

**Cost Overruns**
```bash
# Check current spending
python cli.py stats --db results/app.db --show-costs

# Reset daily limits
python cli.py config --set daily_cost_limit 25.00
```

**Poor Results from Budget APIs**
```bash
# Try next tier up
python cli.py process --engines google,gemini --input photos/ --output results/

# Or focus on specific problem cases
python cli.py process --input photos/ --output results/ \
  --filter "confidence < 0.80" --engine claude
```

### **API-Specific Issues**

**Azure**: Ensure correct region in endpoint URL
**Google**: Service account JSON must be valid and accessible
**AWS**: Check IAM permissions for Textract access
**Gemini**: API key must be from Google AI Studio, not Google Cloud
**OpenAI**: Ensure sufficient credit balance in account
**Claude**: Verify API key is for Claude 3.5, not older models

---

## 📊 **Performance Expectations**

### **Accuracy by API Type**
- **Budget APIs**: 80-85% accuracy (Azure, Google, AWS)
- **Premium APIs**: 90-95% accuracy (Gemini, GPT-4o)
- **Ultra-Premium**: 95-98% accuracy (Claude, GPT-4)

### **Speed by API**
- **Fastest**: Google Vision (~0.5s per image)
- **Fast**: Azure, AWS Textract (~1s per image)
- **Medium**: Gemini, GPT-4o (~2-3s per image)
- **Slower**: Claude, GPT-4 (~3-5s per image)

### **Reliability by Provider**
- **Most Reliable**: Google (Vision & Gemini)
- **Enterprise Grade**: Microsoft Azure, AWS
- **Premium Quality**: Anthropic Claude
- **Versatile**: OpenAI (GPT-4o & GPT-4)

---

**Next Step**: Choose your APIs based on budget and accuracy needs, then run your first batch test!

```bash
# Recommended first test (50 specimens)
python cli.py process --input test_batch/ --output test_results/ \
  --config config/config.windows.toml --max-cost 5.00
```