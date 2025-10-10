# Usage Modes

This system supports different levels of complexity depending on your needs. Choose the mode that fits your project requirements.

## 🚀 **Quick Mode**: Simple OCR Extraction

**Perfect for**: Individual researchers, small projects, immediate data needs

### What you get:
- Direct OCR processing of images
- CSV output ready for immediate use
- No database complexity
- Fastest path from images to data

### Workflow:
```bash
# 1. Process images with OCR
python cli.py process --input specimen_photos/ --output results/

# 2. Check your data (done!)
ls results/
# occurrence.csv          <- Darwin Core data ready for GBIF
# raw.jsonl              <- Raw OCR results with confidence scores
# manifest.json          <- Processing metadata
```

### Use Quick Mode when:
- ✅ You have < 500 images to process
- ✅ You trust the OCR accuracy (Apple Vision: 95%)
- ✅ You don't need detailed review workflows
- ✅ CSV output meets your needs

---

## 🔬 **Research Mode**: Quality Control Workflow

**Perfect for**: Research projects, institutional collections, quality-focused work

### What you get:
- OCR extraction with review interface
- Curator tools for data correction
- Confidence scoring and flagging
- Database tracking of corrections

### Workflow:
```bash
# 1. Extract data with database tracking
python cli.py process --input specimen_photos/ --output results/

# 2. Review extraction results in web interface
python review_web.py --db results/candidates.db --images specimen_photos/
# Opens http://localhost:5000 for side-by-side review

# 3. Export approved data
python cli.py export --output results/ --version 1.0
# Creates dwca_v1.0.zip with reviewed data
```

### Use Research Mode when:
- ✅ Data quality is critical
- ✅ Multiple people need to review results
- ✅ You want to track confidence scores
- ✅ GBIF submission requires quality control

---

## 🏛️ **Production Mode**: Enterprise Compliance

**Perfect for**: Museums, herbaria, institutional digitization programs

### What you get:
- Full audit trails and compliance reporting
- Multiple data source integration
- User authentication and permissions
- Institutional-grade quality control

### Workflow:
```bash
# 1. Process with audit tracking
python cli.py process --input specimen_photos/ --output results/ \\
  --audit-user "curator@institution.edu"

# 2. Import additional data sources (optional)
python cli.py import --input external_data.csv --output results/ \\
  --audit-user "datamanager@institution.edu"

# 3. Multi-user review workflow
python review_web.py --db results/candidates.db --images specimen_photos/ \\
  --auth-required --user-tracking

# 4. Generate compliance reports
python cli.py audit-report --output compliance/ --format institutional

# 5. Export with full provenance
python cli.py export --output results/ --version 2.1 \\
  --include-audit --include-provenance
```

### Use Production Mode when:
- ✅ Institutional compliance requirements exist
- ✅ Multiple curators/data managers involved
- ✅ Audit trails are legally required
- ✅ Long-term data management is critical

---

## 🔀 **Hybrid Mode**: Multiple Data Sources

**Perfect for**: Complex projects combining OCR, manual entry, and existing data

### What you get:
- OCR extraction from images
- Manual data entry interface
- CSV/spreadsheet import capabilities
- Unified review and export workflow

### Workflow:
```bash
# 1. Extract from images
python cli.py process --input new_photos/ --output project_db/

# 2. Import existing CSV data
python cli.py import --input historical_records.csv --output project_db/

# 3. Manual entry for problematic specimens
python review_web.py --db project_db/candidates.db \\
  --images new_photos/ --enable-manual-entry

# 4. Review all data sources together
# Web interface shows OCR, imported, and manual data

# 5. Export unified dataset
python cli.py export --output project_db/ --version final \\
  --include-all-sources
```

### Use Hybrid Mode when:
- ✅ Combining new digitization with existing records
- ✅ Some specimens require manual data entry
- ✅ Multiple data sources need integration
- ✅ Historical data needs cleaning/standardization

---

## 🎯 **Mode Selection Guide**

| Your Situation | Recommended Mode | Key Benefits |
|-----------------|------------------|--------------|
| "I just need data from these photos" | **Quick Mode** | Fastest, simplest |
| "Quality matters more than speed" | **Research Mode** | Review workflow |
| "This is for institutional archives" | **Production Mode** | Compliance, audit |
| "I have photos + existing records" | **Hybrid Mode** | Multiple sources |

## 📊 **Feature Comparison**

| Feature | Quick | Research | Production | Hybrid |
|---------|-------|----------|------------|--------|
| OCR Processing | ✅ | ✅ | ✅ | ✅ |
| CSV Output | ✅ | ✅ | ✅ | ✅ |
| Database Storage | ❌ | ✅ | ✅ | ✅ |
| Web Review Interface | ❌ | ✅ | ✅ | ✅ |
| Confidence Scoring | ❌ | ✅ | ✅ | ✅ |
| Audit Trails | ❌ | ❌ | ✅ | ✅ |
| User Authentication | ❌ | ❌ | ✅ | Optional |
| Multiple Data Sources | ❌ | ❌ | ✅ | ✅ |
| Compliance Reporting | ❌ | ❌ | ✅ | ✅ |
| Manual Data Entry | ❌ | Limited | ✅ | ✅ |

## 🔧 **Configuration Examples**

### Quick Mode Config
```toml
# config/quick.toml
[ocr]
preferred_engine = "vision"
confidence_threshold = 0.70

[export]
formats = ["csv"]
include_raw = false
```

### Research Mode Config
```toml
# config/research.toml
[ocr]
preferred_engine = "vision"
confidence_threshold = 0.80
enable_fallbacks = true

[qc]
flag_low_confidence = true
require_review = true

[export]
formats = ["csv", "dwca"]
include_confidence = true
```

### Production Mode Config
```toml
# config/production.toml
[audit]
required = true
user_tracking = true
retain_days = 2555  # 7 years

[qc]
multi_user_review = true
sign_off_required = true

[export]
formats = ["csv", "dwca", "institutional"]
include_audit = true
include_provenance = true
```

## 🚀 **Getting Started**

1. **Choose your mode** based on your needs
2. **Start with Quick Mode** if unsure
3. **Upgrade to Research/Production** as requirements grow
4. **All modes use the same core commands** - just different options

The architecture is designed to grow with your needs - start simple and add complexity only when required.
