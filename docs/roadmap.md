# Roadmap

Strategic priorities for the herbarium OCR to Darwin Core toolkit.

**Current development focus:** See [GitHub Projects](#project-organization) below for detailed progress tracking across the complete herbarium digitization ecosystem.

## Completed Research Contributions

- **✅ Comprehensive OCR Engine Analysis** — **Primary Research Finding** (September 2025)
  - **Purpose**: Definitive evaluation of OCR engines for herbarium specimen digitization accuracy
  - **Methodology**: Testing on real AAFC-SRDC specimens with advanced preprocessing, statistical analysis
  - **Key Finding**: **Apple Vision achieves 95% accuracy vs Tesseract's 15%** on herbarium specimens
  - **Impact**: Validates Apple Vision as optimal primary OCR engine, eliminates API dependency for 95% of processing
  - **Economic Impact**: $1600/1000 specimens cost savings vs manual transcription
  - **Technical Impact**: Enables production-ready digitization workflow with minimal manual review
  - **Documentation**: [docs/research/COMPREHENSIVE_OCR_ANALYSIS.md](research/COMPREHENSIVE_OCR_ANALYSIS.md)
- **✅ Reproducible Image Access System** — **Research Tool Development** (September 2025)
  - **Purpose**: Developed comprehensive system for reproducible herbarium image referencing to support digitization research
  - **Methodology**: Quality-stratified image categorization with realistic distributions matching institutional collections
  - **Impact**: Enables reproducible testing, collaborative research, and standardized benchmarking across institutions
  - **Components**: S3 integration, automated categorization, test bundle generation, public accessibility framework
  - **Academic Value**: Provides standardized research methodology for herbarium digitization quality assessment
  - **Documentation**: [REPRODUCIBLE_IMAGES_SUMMARY.md](status/REPRODUCIBLE_IMAGES_SUMMARY.md)

## Immediate Priorities - Stakeholder Focused

**Context**: System ready for production deployment, stakeholders need tangible results demonstration.

### Phase 1: MVP Dataset & Stakeholder Demonstration (Week 1)
- **✅ MVP demonstration script ready** - Process 50-100 specimens for stakeholder review
- **✅ Stakeholder progress report** - For Dr. Chrystel Olivier and Dr. Julia Leeson
- **✅ Production system validated** - 95% accuracy on real specimens
- **Ready for deployment** - 2,800 specimens processable immediately

### Phase 2: Full Production Deployment (Weeks 2-3)
- **Process 2,800 captured photos** using validated Apple Vision pipeline
- **Quality control review** with Dr. Julia Leeson (Herbarium Manager)
- **Darwin Core data delivery** - GBIF-ready institutional dataset
- **Complete processing documentation** with audit trail

### Phase 3: Institutional Integration (Weeks 4-6)
- **Database integration** - Transfer to institutional collection systems
- **Staff training completion** - Handover to successor workflows
- **Long-term sustainability** - Ongoing digitization procedures
- **Success metrics validation** - Final project evaluation

See [HANDOVER_PRIORITIES.md](HANDOVER_PRIORITIES.md) for detailed 8-week plan.

## Long-term Development Features

- **Integrate multilingual OCR models for non-English labels** — Future priority ([#138](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/138))
- **Integrate GBIF taxonomy and locality verification into QC pipeline** — Future priority ([#139](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/139))

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

For a complete feature history, see [CHANGELOG.md](changelog.md).

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
