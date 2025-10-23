# Cost Claims Audit & Corrections

**Issue**: Documentation mixes data from different extraction runs, creating misleading claims.

## What Actually Happened

### v1.0: Apple Vision Run (Poor Quality)
- **Specimens processed**: 2,885
- **Quality**: 5.5% scientificName coverage (159/2,885)
- **Cost**: $0 (Apple Vision is free but terrible quality)
- **Status**: FAILED - unusable results

### Phase 1 Baseline: OpenAI GPT-4o-mini (Good Quality)
- **Specimens processed**: 500
- **Quality**: 98% scientificName coverage (490/500)
- **Actual cost**: $1.85 total
- **Per-specimen cost**: $0.0037
- **Status**: SUCCESS - production quality

### OpenRouter Validation: FREE Models (Best Quality)
- **Specimens processed**: 20
- **Quality**: 100% scientificName coverage (20/20)
- **Cost**: $0.00
- **Status**: SUCCESS - better than paid baseline

## Misleading Claims in docs/index.md

### ❌ MISLEADING: "2,885 specimens extracted"
**Reality**: 2,885 were photographed. Only 500 were successfully extracted with quality data.

### ❌ MISLEADING: "Production Extraction (2,885 Specimens)"
**Reality**: This header makes it sound like 2,885 got the 98% quality, but that's from the 500-specimen run.

### ❌ MISLEADING: "$10.55" cost claim
**Reality**: This is an EXTRAPOLATION ($1.85 × 2885/500 ≈ $10.67), not an actual cost incurred.
**Actual cost**: $1.85 for 500 specimens

### ❌ CONFUSING: Mixing baseline runs
The index.md shows:
```markdown
| Provider | Coverage | Cost | Status |
| OpenAI GPT-4o-mini | 98% | $10.55 | Baseline |
| OpenRouter FREE | 100% | $0.00 | Winner |
```

This compares:
- 500 specimens @ 98% quality (real) vs
- 20 specimens @ 100% quality (real)
- But uses extrapolated cost ($10.55) not actual ($1.85)

## Correct Claims

### What We Can Truthfully Say

**✅ ACCURATE**: "500 specimens processed with 98% scientificName coverage at $1.85 cost"

**✅ ACCURATE**: "OpenRouter FREE models achieve 100% coverage (20/20 validation) at $0 cost"

**✅ ACCURATE**: "2,885 specimen photographs available for processing"

**✅ ACCURATE**: "Extrapolated cost for 2,885 specimens would be ~$10.67 with GPT-4o-mini"

**✅ ACCURATE**: "FREE models outperform paid baseline on validation set"

## Recommendations

1. **Separate runs clearly**: Don't mix v1.0 (2,885, failed) with Phase 1 (500, succeeded)

2. **Use actual costs**: Show $1.85 for 500 specimens, note extrapolation separately

3. **Clarify specimen counts**:
   - 2,885 photographed
   - 500 extracted for baseline quality assessment
   - 20 used for OpenRouter validation

4. **Be honest about scale**: We validated the approach works, but haven't processed all 2,885 with the good models yet

## Proposed Fix for docs/index.md

Replace the misleading section with:

```markdown
### Research Results

**Phase 1 Baseline (500 Specimens)**
- Model: OpenAI GPT-4o-mini
- Quality: 98% scientificName coverage (490/500)
- Cost: $1.85 actual ($0.0037 per specimen)

**Validation Study (20 Specimens)**
- Model: Qwen 2.5 VL 72B (FREE)
- Quality: 100% scientificName coverage (20/20)
- Cost: $0.00

**Key Finding**: FREE open-source models outperform paid commercial APIs

**Dataset Size**: 2,885 specimen photographs ready for full-scale processing
**Estimated cost for full dataset**: ~$10.67 with GPT-4o-mini, $0 with FREE models
```

## Data Sources

All claims should cite:
- `full_dataset_processing/published/v1.1.0/phase1_baseline_statistics.json` (500 specimens)
- `full_dataset_processing/published/v1.1.0/README.md` (methodology)
- CHANGELOG.md v1.0 section (2,885 Apple Vision run failure)

---

**Audited**: 2025-10-23
**Status**: Corrections needed in docs/index.md, README.md
