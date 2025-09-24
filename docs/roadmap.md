# Roadmap

Strategic priorities for the herbarium OCR to Darwin Core toolkit.

**Current development focus:** See [GitHub Projects](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/projects) for detailed progress tracking and issue management.

## Critical Features

- **Integrate multilingual OCR models for non-English labels** — High priority, Q2 2025 ([#138](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/138))
- **Integrate GBIF taxonomy and locality verification into QC pipeline** — Medium priority, Q3 2025 ([#139](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/139))

## Issue Management

Create GitHub issues from roadmap entries:

```bash
python scripts/create_roadmap_issues.py --repo <owner>/<repo> \
    --project-owner <owner> --project-number <n>
```

This script keeps the roadmap synchronized with GitHub Projects for automated agent workflows.

## Medium Priority Features

- **Support GPU-accelerated inference for Tesseract** — Q3 2025 ([#186](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/186))
- **Populate mapping rules** in `config/rules/dwc_rules.toml` and `config/rules/vocab.toml` ([#157](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/157))
- **Audit trail for import steps** with explicit user sign-off ([#193](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/193))
- **Add evaluation harness** for GPT prompt template coverage ([#195](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/195))

For a complete feature history, see [CHANGELOG.md](../CHANGELOG.md).
