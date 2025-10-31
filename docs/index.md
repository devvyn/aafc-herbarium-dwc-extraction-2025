# AAFC Herbarium Darwin Core Dataset

**Status**: 🧪 Preview/Beta - Unverified Data
**Version**: v1.0 Vision Baseline
**Records**: 2,702 herbarium specimens
**Last Updated**: October 2025

---

## ⚠️ Important Disclaimer

**This is a PREVIEW dataset for research and testing purposes.**

- ✅ Extracted from AAFC herbarium specimen images using OCR + AI
- ⚠️ **NOT manually verified** - expect errors and incomplete records
- 🧪 Use for algorithm testing, prototyping, and research only
- 🚫 Do NOT use for taxonomic decisions or critical applications

**Accuracy**: ~70-80% on core fields (scientificName, locality). Many records have missing or incorrect data.

---

## 📥 Download Options

### GitHub Releases

| Format | Size | Best For | Download |
|--------|------|----------|----------|
| **CSV** | 606 KB | Spreadsheets, quick analysis | [occurrence.csv](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/releases/download/v1.0-vision-baseline/occurrence.csv) |
| **Darwin Core Archive** | ~650 KB | GBIF, biodiversity platforms | [dwc-archive.zip](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/releases/download/v1.0-vision-baseline/dwc-archive.zip) |
| **JSONL** | 2.5 MB | API integration, confidence scores | [raw.jsonl](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/releases/download/v1.0-vision-baseline/raw.jsonl) |

### S3 Public Bucket (Alternative Access)

```
https://aafc-herbarium-data.s3.amazonaws.com/v1.0/occurrence.csv
https://aafc-herbarium-data.s3.amazonaws.com/v1.0/dwc-archive.zip
https://aafc-herbarium-data.s3.amazonaws.com/v1.0/raw.jsonl
```
*(S3 URLs will be active after upload)*

---

## 📊 Dataset Overview

### Coverage

- **Institution**: Agriculture and Agri-Food Canada (AAFC)
- **Collection**: Saskatoon Research and Development Centre Herbarium
- **Geographic Focus**: Saskatchewan, Canada
- **Basis of Record**: Preserved specimens (herbarium sheets)
- **Records**: 2,702 specimens

### Extraction Method

- **OCR Engine**: Apple Vision API (macOS native)
- **AI Processing**: GPT-4o-mini for Darwin Core field extraction
- **Quality Control**: Automated confidence scoring (not manual verification)
- **Processing Date**: October 2025

---

## 📖 Quick Start

### Download CSV

```bash
wget https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/releases/download/v1.0-vision-baseline/occurrence.csv
```

### Load in Python

```python
import pandas as pd

df = pd.read_csv('occurrence.csv')
print(f"Loaded {len(df)} specimens")

# Filter high-confidence records
high_quality = df[df['ocr_confidence'] > 0.9]
print(f"{len(high_quality)} high-confidence specimens")
```

### Load in R

```r
library(tidyverse)

specimens <- read_csv("occurrence.csv")
nrow(specimens)  # 2702 records
```

---

## 📚 Full Documentation

- **[Data Dictionary](data-dictionary.md)** - Complete field descriptions
- **[Known Issues](known-issues.md)** - Data quality caveats
- **[Usage Examples](examples.md)** - Code snippets and workflows
- **[Source Code](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025)** - GitHub repository

---

## 📧 Contact

**Data Curator**: Devvyn Murphy
**Institution**: Agriculture and Agri-Food Canada - SRDC
**Issues**: [GitHub Issues](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues)

---

## 📄 License

**Dataset**: [CC0 1.0 (Public Domain)](https://creativecommons.org/publicdomain/zero/1.0/)
**Source Code**: MIT License

---

*Last updated: 2025-10-31 | Version: v1.0-vision-baseline | Preview/Beta*
