# Documentation Index

Welcome to the AAFC Herbarium OCR documentation. This system helps you extract structured data from herbarium specimen images.

## 🚀 **Start Here**

### New to the System?
1. **[Main README](../README.md)** - Quick start and overview
2. **[Usage Modes](../USAGE_MODES.md)** - Choose the right complexity level for your project
3. **[Architecture](../ARCHITECTURE.md)** - Understand the dual-layer design

### Ready to Process Images?
1. **[Installation Guide](installation.md)** - Set up your environment
2. **[Quick Start Examples](quickstart_examples.md)** - Common workflows
3. **[OCR Engine Guide](ocr_engines.md)** - Apple Vision, GPT-4, and others

## 📚 **Documentation by Topic**

### **Core Concepts**
- **[Architecture Overview](../ARCHITECTURE.md)** - Extraction vs Curation layers
- **[Specimen Provenance Architecture](SPECIMEN_PROVENANCE_ARCHITECTURE.md)** - v2.0.0 lineage tracking ⭐
- **[Terminology Guide](../TERMINOLOGY_GUIDE.md)** - Clear definitions of confusing terms
- **[Data Flow](data_flow.md)** - Images → OCR → Review → Export

### **Usage Guides**
- **[Usage Modes](../USAGE_MODES.md)** - Quick, Research, Production, Hybrid modes
- **[Workflow Examples](workflow_examples.md)** - Real-world processing scenarios
- **[Quality Control](qc.md)** - Review interface and confidence scoring

### **Technical Reference**
- **[API Reference](api_reference.md)** - Function and class documentation
- **[Configuration](configuration.md)** - TOML settings and options
- **[Database Schema](database_schema.md)** - SQLite table structure

### **Advanced Features**
- **[Export Formats](export_and_reporting.md)** - Darwin Core, GBIF, custom formats
- **[Cloud APIs](cloud_apis.md)** - Google Vision, Azure, AWS Textract setup
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

### **Development**
- **[Contributing](../CONTRIBUTING.md)** - How to contribute to the project
- **[Testing](testing.md)** - Running tests and adding new ones
- **[Release Process](releases.md)** - Version management and deployment

### **Release Documentation (v2.0.0+)**
- **[v2.0.0 Release Plan](RELEASE_2_0_PLAN.md)** - Migration strategy and timeline
- **[v2.0.0 Release Status](status/2025-10-22-v2.0.0-release.md)** - Current status and accomplishments
- **[GBIF Validation Integration](GBIF_VALIDATION_INTEGRATION.md)** - v2.1.0 roadmap (planned)
- **[Archived Status Docs](status/archive/2025-10/)** - Historical v1.x status updates

## 🎯 **Documentation by User Type**

### **Researchers & Students**
- Start with **[Quick Mode](../USAGE_MODES.md#quick-mode-simple-ocr-extraction)**
- Focus on **[OCR Engine Guide](ocr_engines.md)** for accuracy
- Use **[Workflow Examples](workflow_examples.md)** for common tasks

### **Curators & Data Managers**
- Use **[Research Mode](../USAGE_MODES.md#research-mode-quality-control-workflow)**
- Review **[Quality Control Guide](qc.md)** for curator tools
- Check **[Export Formats](export_and_reporting.md)** for GBIF submission

### **IT & System Administrators**
- Deploy using **[Production Mode](../USAGE_MODES.md#production-mode-enterprise-compliance)**
- Review **[Architecture Overview](../ARCHITECTURE.md)** for system design
- Configure using **[Configuration Guide](configuration.md)**

### **Developers**
- Read **[Architecture](../ARCHITECTURE.md)** and **[API Reference](api_reference.md)**
- Follow **[Contributing Guidelines](../CONTRIBUTING.md)**
- Run **[Testing Suite](testing.md)** before submitting changes

## 📋 **Common Questions**

### **"What's the difference between extraction and import?"**
- **Extraction**: Getting data FROM images using OCR
- **Import**: Bringing external CSV/spreadsheet data INTO the database
- See **[Terminology Guide](../TERMINOLOGY_GUIDE.md)** for full definitions

### **"Do I need a database for simple OCR?"**
- **No** - Quick Mode processes images directly to CSV
- **Yes** - If you need review workflows or quality control
- See **[Usage Modes](../USAGE_MODES.md)** for decision guide

### **"Which OCR engine should I use?"**
- **Apple Vision**: 95% accuracy, free on macOS (recommended)
- **Cloud APIs**: Good accuracy, small cost per image
- See **[OCR Engine Guide](ocr_engines.md)** for detailed comparison

### **"How do I submit data to GBIF?"**
- Use Research or Production mode for quality control
- Export creates Darwin Core Archives (.zip files)
- See **[Export Guide](export_and_reporting.md)** for GBIF submission

## 🔧 **Quick Reference**

### **Essential Commands**
```bash
# Extract data from images (most common)
python cli.py process --input photos/ --output results/

# Review extracted data (quality control)
python review_web.py --db results/candidates.db --images photos/

# Export to Darwin Core format (GBIF submission)
python cli.py export --output results/ --version 1.0
```

### **Key Files**
- `occurrence.csv` - Darwin Core specimen records
- `raw.jsonl` - Raw OCR results with confidence scores
- `app.db` - SQLite database (if using Review/Production modes)
- `candidates.db` - Review database for quality control

### **Important Configs**
- `config/config.default.toml` - Main system configuration
- `config/image_sources.toml` - S3 and test image sources
- `.env` - Environment variables (API keys, AWS credentials)

## 📞 **Getting Help**

1. **Check [Troubleshooting Guide](troubleshooting.md)** for common issues
2. **Review [FAQ](faq.md)** for frequently asked questions
3. **Search [GitHub Issues](https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues)** for known problems
4. **Create new issue** if you find a bug or need a feature

---

**Documentation Structure Philosophy**: Start simple (README → Usage Modes), add complexity as needed (Architecture → API Reference), with clear paths for different user types.
