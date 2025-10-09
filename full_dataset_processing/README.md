# Research Data Archive

This directory contains experimental and production processing runs. **Research data is not committed to the repository** to keep it clean and focused on production code.

## Where to Find Research Data

### Published Datasets

**v1.1.0 Release Assets:**
- [GitHub Releases](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/releases/tag/v1.1.0)
  - `phase1_baseline_statistics.json` - 500 specimen OpenAI baseline
  - `openrouter_validation_results.json` - 20 specimen FREE model validation
  - Quality comparison reports

### Experimental Results

**Available on request or in local development archives:**
- Phase 1 baseline (OpenAI GPT-4o-mini, 500 specimens)
- Prompting experiments (CoT, Few-Shot, OCR-First, 10 specimens each)
- Production runs (v1 batches 1-3)
- Validation sets (v1 and v3, 50 specimens each)

### Regenerating Research Data

All experimental data is regenerable from scripts:

```bash
# Regenerate baseline results
uv run python scripts/submit_batch.py --input batch_input.jsonl

# Regenerate OpenRouter extraction
uv run python scripts/extract_openrouter.py \
  --input /path/to/images \
  --output phase1_baseline \
  --model qwen-vl-72b-free
```

## Directory Structure (Local Development)

When working locally, experimental data lives here:

```
full_dataset_processing/
├── README.md                          # This file
├── .gitkeep                          # Preserve directory in git
├── published/                        # Curated datasets (committed)
│   └── v1.1.0/
│       ├── baseline_statistics.json
│       └── validation_results.json
├── phase1_baseline/                  # NOT committed
├── gpt4omini_batch_cot/             # NOT committed
├── gpt4omini_batch_few_shot/        # NOT committed
└── ... (other experiments)
```

**Note:** Only `README.md`, `.gitkeep`, and `published/` are committed to version control.

## Why Research Data Isn't in the Repository

**Reasons:**
1. **Repository size** - Research data is large (GB), code is small (MB)
2. **Regenerability** - All data can be regenerated from scripts
3. **Version control** - Git is for code, not data
4. **Clarity** - Keeps repo focused on production-ready code

**Best practices:**
- Commit scripts and configuration
- Publish curated datasets as GitHub release assets
- Archive working data locally or in separate research repositories
- Document methodology, not raw outputs

## For Researchers

If you need access to full experimental datasets:
1. Check [GitHub Releases](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/releases)
2. Regenerate from scripts (instructions above)
3. Contact maintainers for specific datasets

## For Contributors

When adding new experiments:
1. Place output in `full_dataset_processing/experiment_name/`
2. Do NOT commit experimental data (already in .gitignore)
3. Document methodology in `docs/research/`
4. Publish curated results as release assets when appropriate

---

**For complete documentation:** See [docs/research/methodology.md](../docs/research/methodology.md)
