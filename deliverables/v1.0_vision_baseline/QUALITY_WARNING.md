# ⚠️ Quality Warning - v1.0 Vision API Baseline

**Dataset**: AAFC Herbarium Darwin Core Extraction v1.0
**Extraction Date**: 2025-10-04
**Status**: BASELINE QUALITY - Use with caution

---

## Quality Assessment Summary

**Overall Grade**: ⚠️ **C (Baseline)** - Suitable for exploration, NOT recommended for publication without manual review

### Field Coverage

| Field | Coverage | Grade | Notes |
|-------|----------|-------|-------|
| scientificName | 81.2% (2,343/2,885) | ⚠️ C | **Below publication threshold** |
| catalogNumber | 31.7% (915/2,885) | ❌ F | **Critically low** |
| country | 77.2% (2,229/2,885) | ⚠️ C+ | Acceptable |
| stateProvince | 77.2% (2,229/2,885) | ⚠️ C+ | Acceptable |
| eventDate | 63.6% (1,836/2,885) | ⚠️ D | Low |
| recordedBy | 10.3% (296/2,885) | ❌ F | **Very poor** |
| locality | 12.9% (372/2,885) | ❌ F | **Very poor** |

**Quality threshold for GBIF publication**:
- ✅ Minimum: ≥75% scientificName coverage
- ❌ Good: ≥90% scientificName, ≥80% catalogNumber
- ❌ Excellent: ≥98% scientificName, ≥95% catalogNumber

**This dataset meets MINIMUM threshold only.**

---

## Known Issues

### 1. OCR Recognition Errors

**Problem**: Apple Vision API struggles with handwritten labels and complex layouts

**Examples from actual data**:
```csv
recordedBy: "Baedten dny" (should be collector name)
recordedBy: "Wheat ilield" (OCR misread)
recordedBy: "Chacker by" (should be "Checked by")
scientificName: "Identified by" (extracted wrong field)
scientificName: "Habitab collector" (OCR error + wrong field)
locality: "Marn Lanke Ram MoaFin Habitab" (garbled text)
```

**Impact**:
- Scientific names often extracted from wrong label sections
- Collector names highly unreliable
- Locality data frequently garbled

### 2. Missing Critical Fields

**catalogNumber coverage: 31.7%** - This is a CRITICAL failure for herbarium data.

**Why this matters**:
- Catalog numbers are primary keys for specimen tracking
- Required for linking to institutional databases
- Essential for data quality control

**Root cause**: Vision API does not reliably detect catalog number patterns (numeric codes, accession numbers).

### 3. Low Confidence on Handwritten Text

**Problem**: Handwritten labels (common in historical herbarium specimens) show very poor recognition.

**Evidence**:
- Empty OCR text: 183 specimens (6.3%)
- High OCR confidence but wrong extraction: common
- Mixed handwriting/print: poor results

---

## Comparison to High-Quality Alternative

### OpenRouter Qwen 2.5 VL 72B (Validated)

**Test results** (20-specimen validation, v1.1.0):
- ✅ scientificName: **100%** coverage (vs 81.2% Vision)
- ✅ Cost: **$0.00** (FREE tier, same as Vision)
- ✅ Quality: Consistently superior on same specimens

**Conclusion**: OpenRouter provides significantly better quality at identical cost.

---

## Recommended Use Cases

### ✅ Acceptable Uses

1. **Exploratory Data Analysis**
   - Get rough sense of collection composition
   - Identify specimen categories (preserved vs living)
   - Geographic distribution overview (country/province level)

2. **Quality Baseline**
   - Establish improvement metrics
   - Compare OCR engine performance
   - Validate extraction pipeline functionality

3. **Research Methodology**
   - Document extraction challenges
   - Publish quality comparison studies
   - Benchmark future improvements

### ❌ NOT Recommended

1. **Direct GBIF Publication**
   - 81% scientificName coverage insufficient for biodiversity research
   - Catalog number field too sparse (32%)
   - High error rate requires extensive manual review

2. **Institutional Database Import**
   - Unreliable catalog numbers create reconciliation problems
   - Scientific name errors propagate to downstream systems
   - Collector attribution mostly missing/wrong

3. **Scientific Research**
   - Taxonomic accuracy unverified
   - Geographic precision questionable
   - Temporal data (eventDate) only 64% coverage

---

## Improvement Plan

### Immediate: v2.0 OpenRouter Production

**Status**: Ready to process

**Expected improvements**:
- scientificName: 81% → **>98%** (+17 percentage points)
- catalogNumber: 32% → **>90%** (+58 percentage points)
- Overall quality: Baseline → **Production-ready**

**Timeline**: 4-6 hours processing time

**Cost**: $0.00 (FREE tier)

### Future: v3.0 Manual Review + Validation

**Approach**:
- Start with v2.0 high-quality extraction
- Dr. Leeson scientific review
- Manual corrections for edge cases
- GBIF validation API integration

**Expected outcome**: Research-grade dataset (>99% accuracy)

---

## Data Transparency Statement

**Why publish low-quality v1.0?**

1. **Scientific Integrity**: Show all data, document quality honestly
2. **Methodology Transparency**: Researchers can see what didn't work
3. **Reproducibility**: Others can validate our quality assessments
4. **Progress Documentation**: Clear improvement path v1.0 → v2.0 → v3.0

**Best practice**: Always publish with clear quality documentation, even when imperfect.

---

## Citation

If using this dataset, please cite with quality warning:

```
AAFC Herbarium Darwin Core Extraction v1.0 (Baseline Quality - Apple Vision API)
Extracted: 2025-10-04
Coverage: 81.2% scientificName, 31.7% catalogNumber
Quality Grade: C (Baseline)
⚠️ Manual review recommended before research use
Available: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/releases
```

---

## Contact

**Questions about data quality?**
- GitHub Issues: https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues
- Documentation: https://aafc.devvyn.ca

**For scientific validation questions:**
- Contact: Dr. Julia Leeson (Herbarium Manager, AAFC-SRDC)

---

**Last Updated**: 2025-10-24
**Next Quality Milestone**: v2.0 OpenRouter Production (in progress)
