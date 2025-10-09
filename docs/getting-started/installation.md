# Installation

Get started with Herbarium DWC Extraction in minutes.

---

## Requirements

- **Python:** 3.11 or higher
- **Disk space:** ~1GB for dependencies, ~5GB for image cache
- **Memory:** 4GB minimum (8GB recommended for large batches)
- **OS:** macOS (recommended), Linux, Windows

---

## Quick Install

```bash
# Clone repository
git clone https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025.git
cd aafc-herbarium-dwc-extraction-2025

# Install dependencies
./bootstrap.sh

# Verify installation
python cli.py --help
```

---

## Platform-Specific Setup

### macOS (Recommended)

✅ **Apple Vision API works out-of-the-box** (FREE, no API keys required)

```bash
# Check available engines
python cli.py check-deps

# Expected output:
# ✓ Apple Vision - Available (FREE)
# ✓ Python environment - OK
```

### Linux/Windows

Requires cloud API keys for vision extraction.

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Add API keys to `.env`:**
   ```bash
   # OpenAI (for GPT-4o-mini extraction)
   OPENAI_API_KEY="your-key-here"

   # OpenRouter (for FREE models - recommended)
   OPENROUTER_API_KEY="your-key-here"

   # Optional: Other providers
   # ANTHROPIC_API_KEY=""
   # GOOGLE_API_KEY=""
   ```

3. **Get API keys:**
   - [OpenAI API](https://platform.openai.com/api-keys)
   - [OpenRouter](https://openrouter.ai/keys) - FREE tier available

---

## Development Setup

For contributors and developers:

```bash
# Install with dev dependencies
uv sync

# Run tests
pytest

# Run linter
ruff check . --fix

# Build documentation
mkdocs serve
```

---

## Docker Installation (Optional)

```bash
# Build image
docker build -t herbarium-dwc .

# Run extraction
docker run -v $(pwd)/photos:/photos \
           -v $(pwd)/results:/results \
           -e OPENAI_API_KEY=$OPENAI_API_KEY \
           herbarium-dwc \
           python cli.py process --input /photos --output /results
```

---

## Verification

Test your installation:

```bash
# Check all dependencies
python cli.py check-deps

# Run test extraction (if you have sample images)
python cli.py process --input test_images/ --output test_results/ --limit 1
```

---

## Troubleshooting

### Common Issues

**1. `uv` command not found**

Install `uv` package manager:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**2. Python version mismatch**

Ensure Python 3.11+:
```bash
python --version  # Should be 3.11 or higher

# If not, install via:
# macOS: brew install python@3.11
# Ubuntu: sudo apt install python3.11
# Windows: Download from python.org
```

**3. Apple Vision not available**

Apple Vision only works on macOS. On other platforms, use cloud APIs.

**4. Out of memory errors**

Reduce batch size:
```bash
python cli.py process --input photos/ --output results/ --batch-size 10
```

---

## Next Steps

After installation, you can:

- **Run your first extraction** - Use the Quick Install example above
- **Explore sample code** - Check `examples/` directory in the repository
- **Review documentation** - See the [GitHub README](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025) for complete usage guide
