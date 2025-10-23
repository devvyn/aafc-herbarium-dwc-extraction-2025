# Tomorrow's Session Plan

**Date**: 2025-10-07 (Morning)
**Estimated Time**: 1-2 hours interactive + overnight batch completion

## 🎯 What's Ready Now

### ✅ Interactive CLI Correction Tool
```bash
# Test with baseline results (10 specimens)
uv run python scripts/correct_interactive.py \
  --input full_dataset_processing/gpt4omini_batch/raw.jsonl \
  --output full_dataset_processing/gpt4omini_batch/corrected.jsonl \
  --images /tmp/imgcache
```

**Features**:
- Image preview in terminal
- GBIF autocomplete for scientific names
- Keyboard shortcuts (s=scientificName, c=catalogNumber, etc.)
- Character-by-character expert review
- Creates ground truth for comparison

### ✅ Strategy Comparison Framework
```bash
# When experimental batches complete (12-20 hours)
uv run python scripts/compare_strategies.py \
  --ground-truth full_dataset_processing/gpt4omini_batch/corrected.jsonl \
  --experiments experiments.json \
  --output comparison_results.json
```

**Compares**:
1. Baseline (AAFC-optimized) ← **COMPLETED**
2. Few-shot learning ← Running
3. Chain-of-thought ← Running
4. OCR-first ← Running

### ✅ Experiment Orchestrator
```bash
# Check status anytime
uv run python scripts/experiment_orchestrator.py --status

# When complete, download and compare
uv run python scripts/experiment_orchestrator.py --compare
```

## 🔄 What's Running (Background)

### Batch API Experiments (12-20 hours to complete)

| Strategy | Batch ID | Status | ETA |
|----------|----------|--------|-----|
| Baseline | `batch_68e47d3796d08190b99e9e73fd5aca52` | ✅ COMPLETE | Done |
| Few-shot | `batch_68e49bae521481908a0b32643a10537d` | ⏳ Running | ~6-18 hrs |
| COT | `batch_68e49bb12da88190a2b1fc66b41582f3` | ⏳ Running | ~6-18 hrs |
| OCR-first | `batch_68e49bb3a2a08190be062ce3750c6f33` | ⏳ Running | ~6-18 hrs |

### Free Tier Extraction (Slow trickle)
- Shell: `0f009e`
- Output: `full_dataset_processing/gpt4omini_aafc_free/`
- Rate: ~180 specimens/hour (3 RPM limit)

## 📋 Morning Session Workflow

### 1. Expert Review of Baseline (30-60 min)

**Goal**: Create high-quality ground truth for comparison

```bash
# Launch interactive CLI
uv run python scripts/correct_interactive.py \
  --input full_dataset_processing/gpt4omini_batch/raw.jsonl \
  --output full_dataset_processing/gpt4omini_batch/corrected.jsonl \
  --images /tmp/imgcache
```

**Your task**:
- Review all 10 baseline specimens character-by-character
- Use GBIF autocomplete for scientific names
- Correct catalogNumber, recordedBy, locality, etc.
- This becomes ground truth for comparing strategies

**Time**: ~5 min per specimen = 50 min total

### 2. Check Experimental Batch Status (5 min)

```bash
# Check if batches completed overnight
uv run python scripts/experiment_orchestrator.py --status
```

**If complete**:
- Proceed to comparison
- Select winner
- Submit production batch

**If still running**:
- Come back later in the day
- Continue with other tasks

### 3. Compare Strategies (When complete) (30 min)

```bash
# Automated comparison
uv run python scripts/compare_strategies.py \
  --ground-truth full_dataset_processing/gpt4omini_batch/corrected.jsonl \
  --experiments experiments.json \
  --output comparison_results.json
```

**Outputs**:
- Overall accuracy table (exact, partial)
- Per-field performance (scientificName, catalogNumber, etc.)
- Winner recommendation
- Confidence scores

**Decision point**: Select winning strategy for production

## 🚀 Production Batch Submission (When ready)

### Option A: Full Dataset (2885 specimens, $0.80)
```bash
# Create batch with winning strategy
uv run python scripts/create_batch_request.py \
  --input /tmp/imgcache \
  --output full_dataset_processing/gpt4omini_production \
  --task <winning_strategy> \
  --prompt-dir config/prompts

# Submit
uv run python scripts/submit_batch.py \
  --input full_dataset_processing/gpt4omini_production/batch_input.jsonl
```

### Option B: Partial Dataset (1500 specimens, $0.42)
```bash
# Test on larger subset first
uv run python scripts/create_batch_request.py \
  --input /tmp/imgcache \
  --output full_dataset_processing/gpt4omini_production \
  --limit 1500 \
  --task <winning_strategy> \
  --prompt-dir config/prompts
```

## 💰 Budget Status

```
Fast Lane (learning):
  Baseline:      $0.03 ✅ Complete
  Few-shot:      $0.03 ⏳ Running
  COT:           $0.03 ⏳ Running
  OCR-first:     $0.03 ⏳ Running
  ──────────────────────
  Spent:         $0.12 / $2.00

Slow Lane (production):
  Available:     $4.00
  Options:
    - 1500 specimens: $0.42
    - 2885 specimens: $0.80
    - Reserve: $3.20-$3.58 for iterations
```

## 📊 What Success Looks Like

### Morning:
- [x] 10 baseline specimens corrected (ground truth created)
- [x] Experimental batches complete
- [x] Strategy comparison shows clear winner
- [x] Production batch submitted

### Evening:
- [x] Production batch completes (12-20 hours)
- [x] Validation shows >70% accuracy
- [x] Ready for GBIF export

## 🛠️ Tools Quick Reference

```bash
# CLI Correction
scripts/correct_interactive.py

# Batch Status
scripts/experiment_orchestrator.py --status

# Comparison
scripts/compare_strategies.py

# Create Batch
scripts/create_batch_request.py

# Submit Batch
scripts/submit_batch.py

# Monitor Batch
scripts/monitor_batch.py --batch-id <id>

# Process Results
scripts/process_batch_results.py --batch-id <id>
```

## 📝 Optional: Future Work (If time)

1. **Public Derivatives Pipeline**
   - Downsample images to 1024px
   - Upload to public S3 bucket or CloudFront

2. **CI/CD Workflows**
   - PR validation (test prompt changes)
   - Scheduled extraction (weekly improvements)
   - Release automation

3. **ABCD Schema Implementation**
   - Download ABCD 2.06 XML
   - Map institutional metadata fields
   - Dual export (Darwin Core + ABCD)

## ⚠️ Known Issues

1. **Free tier extraction**: Error with missing prompts (image_to_dwc_v2_aafc.user.prompt) - can ignore, baseline batch is better quality
2. **Multiple background processes**: Several shells running, can clean up if needed
3. **Untracked test directories**: Ignore `test_*` directories for now

## 🎯 End Goal

By end of tomorrow:
- Production-quality extraction of 1500-2885 specimens
- Validated against expert-reviewed ground truth
- Ready for GBIF publication
- Cost: <$1.00
- Time: 24-36 hours total

---

**Ready to start**: Launch CLI correction tool and review those 10 baseline specimens! 🚀
