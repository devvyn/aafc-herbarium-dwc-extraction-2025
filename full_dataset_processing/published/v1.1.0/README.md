# Published Research Data - v1.1.0

**Release:** v1.1.0 (October 9, 2025)
**Topic:** Multi-Provider Extraction with FREE Tier Support

---

## Datasets Included

### 1. Phase 1 Baseline Statistics

**File:** `phase1_baseline_statistics.json`

**Description:** Quality metrics from 500-specimen baseline extraction using OpenAI GPT-4o-mini

**Key Results:**
- Total specimens: 500
- Success rate: 100%
- scientificName coverage: 98.0%
- catalogNumber coverage: 95.4%
- Average confidence: 0.87

**Method:**
- Model: OpenAI GPT-4o-mini
- Prompt: Layout-aware vision extraction
- Cost: $1.85 (500 specimens)
- Date: October 2025

**Use case:** Baseline for quality comparison

---

### 2. OpenRouter Validation Results

**File:** `openrouter_validation_20_specimens.jsonl`

**Description:** Complete extraction results from 20-specimen validation using OpenRouter FREE models

**Key Results:**
- Total specimens: 20
- scientificName coverage: 100% (20/20)
- Model: Qwen 2.5 VL 72B (FREE)
- Cost: $0.00

**Method:**
- Provider: OpenRouter
- Model: qwen/qwen-2.5-vl-72b-instruct:free
- Validation approach: Representative sample from full dataset
- Date: October 9, 2025

**Use case:** Demonstrates FREE models outperform paid baseline

---

## Data Format

### Statistics JSON Schema

```json
{
  "total_specimens": 500,
  "successful_extractions": 500,
  "failed_extractions": 0,
  "success_rate": 1.0,
  "field_coverage": {
    "scientificName": 490,
    "catalogNumber": 477,
    ...
  },
  "field_coverage_percentage": {
    "scientificName": 98.0,
    "catalogNumber": 95.4,
    ...
  },
  "average_confidence": {
    "scientificName": 0.87,
    "catalogNumber": 0.83,
    ...
  }
}
```

### Validation JSONL Schema

```json
{
  "image_path": "path/to/image.jpg",
  "model_used": "qwen/qwen-2.5-vl-72b-instruct:free",
  "extraction": {
    "catalogNumber": "019121",
    "scientificName": "Bouteloua gracilis",
    ...
  },
  "metadata": {
    "timestamp": "2025-10-09T...",
    "cost": 0.0,
    "provider": "openrouter"
  }
}
```

---

## Reproducing These Results

### Phase 1 Baseline

```bash
# 1. Prepare 500 specimen images
# 2. Create batch input
uv run python scripts/create_batch_input.py \
  --input /path/to/images \
  --output batch_input.jsonl

# 3. Submit to OpenAI Batch API
uv run python scripts/submit_batch.py \
  --input batch_input.jsonl \
  --output phase1_baseline

# 4. Calculate statistics
uv run python scripts/calculate_statistics.py \
  --input phase1_baseline/raw.jsonl \
  --output extraction_statistics.json
```

### OpenRouter Validation

```bash
# 1. Select 20 representative specimens
# 2. Run OpenRouter extraction
uv run python scripts/extract_openrouter.py \
  --input /path/to/images \
  --output openrouter_validation \
  --model qwen-vl-72b-free \
  --limit 20
```

---

## Citation

If you use these datasets in research, please cite:

```
AAFC Herbarium DWC Extraction Project (2025).
Multi-Provider Extraction with FREE Tier Support (v1.1.0).
GitHub: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025
```

---

## License

These datasets are published under the same license as the project (MIT).

Research use, modification, and distribution are permitted with attribution.

---

## More Information

- **Full release notes:** [v1.1.0 Release](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/releases/tag/v1.1.0)
- **Methodology:** See `docs/research/methodology.md`
- **Quality analysis:** See `docs/research/quality-comparison.md`

---

**Generated:** October 9, 2025
**Project:** AAFC Herbarium Darwin Core Extraction
