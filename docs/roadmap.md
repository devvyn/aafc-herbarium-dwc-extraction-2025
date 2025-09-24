# Roadmap

Strategic priorities for the herbarium OCR to Darwin Core toolkit.

**Current development focus:** See [GitHub Projects](#project-organization) below for detailed progress tracking across the complete herbarium digitization ecosystem.

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

## Project Organization

The AAFC herbarium digitization project spans multiple domains requiring coordinated development across several GitHub Projects:

### [🏗️ AAFC Herbarium Infrastructure](https://github.com/users/devvyn/projects/5)
**Focus**: Deployment, operations, and production workflows
- Import audit workflows and compliance
- Configuration management and deployment automation
- Production monitoring and system integration
- Multi-repository orchestration and CI/CD pipelines

### [💻 AAFC Herbarium Core Development](https://github.com/users/devvyn/projects/6)
**Focus**: Core toolkit features and technical enhancements
- OCR engine improvements (GPU acceleration, multilingual support)
- Schema parsing and mapping automation
- Development tooling and testing infrastructure
- Performance optimization and technical debt

### [📊 AAFC Herbarium Data & Research](https://github.com/users/devvyn/projects/7)
**Focus**: Data quality, analysis, and research workflows
- GBIF integration and taxonomic validation
- Geographic data verification and gazetteer services
- Export formats and reporting tools
- Research collaboration and data publication

### [📋 Legacy Project](https://github.com/users/devvyn/projects/4)
**Status**: Being reorganized into the new structure above

This multi-project structure supports the full scope of herbarium digitization beyond just code development, enabling coordinated progress across infrastructure deployment, research workflows, and institutional integration.
