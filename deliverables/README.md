# AAFC Herbarium Darwin Core Extraction - Deliverables

## v1.0 Vision API Baseline (October 6, 2025)

**File:** `v1.0_vision_api_baseline.jsonl`
**Specimens:** 2,885 herbarium images
**Extraction Method:** Apple Vision API (FREE)
**Cost:** $0
**Processing Time:** ~1 hour

### Extracted Fields (7 Darwin Core Terms)

| Field | Description | Coverage |
|-------|-------------|----------|
| `catalogNumber` | Specimen institutional ID | ~50% |
| `scientificName` | Taxonomic identification | ~5.5% |
| `eventDate` | Collection date | Variable |
| `recordedBy` | Collector name | Variable |
| `locality` | Collection location | Variable |
| `stateProvince` | Province/state | ~58% |
| `country` | Country of origin | ~58% |

### Quality Metrics

- **Exact matches:** 0% (based on 20-specimen validation)
- **Partial matches:** ~10-15%
- **Known limitations:** OCR accuracy on handwritten labels, field completeness varies

### Data Format

Each line is a JSON object:
```json
{
  "run_id": "2025-10-05T21:17:58.750811+00:00",
  "image": "abc123.jpg",
  "sha256": "abc123...",
  "engine": "vision",
  "engine_version": "1.0",
  "dwc": {
    "catalogNumber": "019121",
    "scientificName": "Bouteloua gracilis",
    "eventDate": "1969-08-14",
    "recordedBy": "J. Looman",
    "locality": "Beaver River crossing",
    "stateProvince": "Saskatchewan",
    "country": "Canada"
  },
  "flags": [],
  "errors": []
}
```

## Upgrade Path

### v2.0 Enhanced Extraction (Available)

**Method:** GPT-4o-mini with layout-aware prompts
**Cost:** $1.60 total ($0.0006 per specimen)
**Fields:** 16 Darwin Core terms (9 additional fields)
**Expected Quality:** Significant improvement

#### Additional Fields in v2.0
- `habitat` - Ecosystem type (native prairie, etc.)
- `minimumElevationInMeters` - Elevation data
- `recordNumber` - Collector's field number
- `identifiedBy` - Taxonomic determiner
- `verbatimLocality` - Exact locality text as written
- Plus 4 more identification/locality fields

#### To Run v2.0 Extraction

**Option A: Free Tier (15-20 hours)**
```bash
python cli.py process \
  --input /tmp/imgcache \
  --output full_dataset_processing/gpt4omini_full \
  --config config/config.gpt4omini.toml
```

**Option B: Paid Tier (1-2 hours, requires OpenAI billing)**
1. Add payment method to OpenAI account
2. Run same command as Option A
3. Cost: $1.60 total

**Option C: Batch API (24 hours, 50% discount)**
```bash
# Implementation required - see docs/batch_api_guide.md
# Cost: $0.80 total
```

## Architecture: "Consider All Means Accessible"

This extraction system is designed with a **plugin architecture** that can leverage:

### Currently Available
- ✅ Apple Vision API (FREE, 7 fields)
- ✅ GPT-4o-mini (PAID, 16 fields)
- ✅ Rules engine (text → DWC mapping)
- ✅ Tesseract OCR (FREE fallback)
- ✅ OCR result caching

### Future Expansion Possibilities
- 🔄 Anthropic Claude (vision + reasoning)
- 🔄 Google Gemini (multimodal)
- 🔄 Ensemble voting (multi-engine consensus)
- 🔄 Progressive enhancement (FREE → PAID for low confidence)
- 🔄 External database matching (iNaturalist, GBIF)
- 🔄 Human-in-loop validation
- 🔄 Batch processing optimization
- 🔄 Agent-managed pipeline composition

### Agent-Managed Pipeline Vision

The system architecture supports **dynamic pipeline composition** where an agent:

1. **Evaluates constraints** (budget, deadline, quality needs)
2. **Inventories available means** (free engines, paid APIs, external services)
3. **Composes optimal pipeline** (cost-aware routing, quality optimization)
4. **Executes and monitors** (progressive enhancement, auto-fallback)

Example decision logic:
```python
if budget == 0:
    return ["vision", "rules"]  # v1.0 approach

if quality == "high" and budget >= 1.60:
    return ["gpt_direct"]  # v2.0 approach

if deadline == "flexible":
    return ["vision", "validate", "gpt_if_needed"]  # Hybrid
```

This enables the system to **consider all means accessible in the world** and choose the best approach for any given situation.

## Usage Recommendations

### Ship v1.0 If:
- ✅ Zero budget required
- ✅ 7 core fields sufficient
- ✅ Acceptable OCR accuracy for initial dataset
- ✅ Can document limitations for stakeholders

### Upgrade to v2.0 If:
- ✅ $1.60 budget available (or can wait 15-20 hours on free tier)
- ✅ Need all 16 fields (habitat, elevation, etc.)
- ✅ Require improved accuracy for publication/research
- ✅ Layout-aware extraction valuable (TOP vs BOTTOM label distinction)

### Consider Hybrid If:
- ✅ Want to validate improvement before full investment
- ✅ Only specific specimens need enhanced extraction
- ✅ Can iterate based on results

## Files Included

```
deliverables/
├── README.md                           # This file
├── v1.0_vision_api_baseline.jsonl      # 2,885 specimens (Vision API)
└── validation/
    └── human_validation.jsonl          # 20 specimens (ground truth)
```

## Validation Data

Ground truth validation available at:
`full_dataset_processing/run_20251005_151758/human_validation.jsonl`

- 20 specimens manually validated
- Corrections documented
- Serves as accuracy baseline

## Technical Documentation

- **Full analysis:** See `Desktop/20251006170409--0600-herbarium-extraction-complete-analysis.md`
- **API setup:** See `API_SETUP_QUICK.md`
- **Configuration:** See `config/config.gpt4omini.toml`
- **Prompts:** See `config/prompts/image_to_dwc_v2.*.prompt`

## Contact & Support

For questions about:
- **Data quality:** Review validation file and analysis docs
- **Upgrade options:** See cost analysis in technical docs
- **Custom extraction:** System supports arbitrary pipeline composition
- **Integration:** Plugin architecture enables new engines/services

---

**Note:** This system embodies the principle of "considering all means accessible in the world" - it can be extended to use any vision API, ensemble multiple engines, leverage external databases, or compose custom pipelines based on specific constraints and goals.

*Generated with enthusiastic precision by Claude Code* 🎯
*October 6, 2025*
