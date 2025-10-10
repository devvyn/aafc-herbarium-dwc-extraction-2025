# Terminology Guide

## The Problem

This project evolved from a simple OCR script to an enterprise data platform, creating **terminology confusion** that obscures the actual workflows. Terms like "import" suggest database operations when we're actually doing OCR extraction.

## Clear Definitions

### **Primary Workflow Terms**

| Term | Definition | Usage | Examples |
|------|------------|-------|----------|
| **Extract** | Getting data FROM images via OCR | `python cli.py process` | Images → Text data |
| **Process** | General term for OCR extraction | `python cli.py process` | Same as extract |
| **Ingest** | Adding data TO the system (any source) | General term | Images, CSV, manual entry |
| **Import** | Bringing external data INTO database | `python cli.py import` | CSV → Database |
| **Export** | Creating output FROM database | `python cli.py export` | Database → Darwin Core |

### **Data Flow Terms**

| Term | What It Describes | Input → Output |
|------|-------------------|----------------|
| **OCR Pipeline** | Image processing workflow | Images → Raw text |
| **Extraction Job** | Complete OCR processing task | Image batch → Structured data |
| **Review Workflow** | Quality control process | Raw data → Approved data |
| **Archive Creation** | Standards compliance export | Database → Darwin Core ZIP |

### **Database Terms**

| Table/Concept | Purpose | Contains |
|---------------|---------|----------|
| **specimens** | Tracks OCR extraction jobs | Image files and their processing status |
| **final_values** | Curator-approved field values | Reviewed and corrected OCR results |
| **processing_state** | OCR job progress tracking | Success/failure status for each image |
| **import_audit** | External data import tracking | Records from CSV imports, not OCR |

## Common Confusions Fixed

### **"Import" Confusion**
**Before**: Issue #193 talks about "import audit sign-off workflow"
**After**: This should be split into:
- **Extraction Audit**: Tracking OCR processing (images → data)
- **Import Audit**: Tracking external data imports (CSV → database)

### **"Specimen" vs "Image" Confusion**
**Before**: `specimens` table suggests biological specimens
**After**: This tracks **extraction jobs** - each record represents processing one image file
- One specimen (biological) might have multiple images
- One image might show multiple specimens
- The table tracks processing, not taxonomy

### **Review Workflow Confusion**
**Before**: `import_review.py` suggests reviewing imports
**After**: This should be `extraction_review.py` - reviewing OCR results

## Recommended Refactoring

### **File Renames**
```bash
# Current → Proposed
import_review.py → extraction_review.py
test_import_review.py → test_extraction_review.py
```

### **Function Renames**
```python
# Current → Proposed
import_review_selections() → review_extractions()
import_audit_trail() → extraction_audit_trail()
```

### **CLI Command Clarity**
```bash
# Current (confusing)
python cli.py process --input images/  # What does "process" mean?

# Clearer
python cli.py extract --input images/  # OCR extraction from images
python cli.py import --input data.csv  # Import external data
```

### **Issue Terminology Updates**

**Issue #193**: "Import audit sign-off workflow"
Should be: "Extraction audit and import audit workflows"

**Issue #194**: "Spreadsheet pivot-table reporting"
Context: This is about reviewing OCR results, not importing spreadsheets

## Usage Examples with Clear Terminology

### **OCR Extraction** (Primary Use Case)
```bash
# Extract data from herbarium images using OCR
python cli.py extract --input specimen_photos/ --output results/

# What happens:
# 1. Images are processed via Apple Vision OCR
# 2. Text data is extracted and structured
# 3. Results saved to results/occurrence.csv
```

### **Data Import** (Secondary Use Case)
```bash
# Import external CSV data into the database
python cli.py import --input external_data.csv --output results/

# What happens:
# 1. CSV data is read and validated
# 2. Records are inserted into database
# 3. Audit trail records the import source
```

### **Review Workflow** (Quality Control)
```bash
# Review extracted OCR results for accuracy
python review_web.py --db results/candidates.db --images specimen_photos/

# What happens:
# 1. Web interface shows side-by-side image and extracted data
# 2. Curator can edit/approve/reject each field
# 3. Approved data goes to final_values table
```

### **Export** (Standards Compliance)
```bash
# Export approved data to Darwin Core format
python cli.py export --output results/ --version 1.0

# What happens:
# 1. Approved data from final_values table
# 2. Formatted according to Darwin Core standards
# 3. Packaged as GBIF-ready archive
```

## Documentation Structure with Clear Terms

### **README.md Focus**
```markdown
# Quick Start: Extract Data from Specimen Images

1. python cli.py extract --input photos/ --output results/
2. python review_web.py --db results/candidates.db --images photos/
3. python cli.py export --output results/
```

### **ADVANCED.md for Complex Workflows**
```markdown
# Advanced: Multiple Data Sources

## OCR Extraction + Manual Data Entry + CSV Import
1. Extract from images: python cli.py extract ...
2. Import CSV data: python cli.py import ...
3. Manual entry via web interface
4. Review all sources together
5. Export to Darwin Core
```

## Benefits of Clear Terminology

### **For New Users**
- Immediately understand that primary workflow is OCR extraction
- Know when they need database features vs simple extraction
- Clear mental model of data flow

### **For Developers**
- Functions and files clearly indicate their purpose
- Separation between extraction and import logic
- Easier to find relevant code

### **For Issues and Planning**
- Features can be categorized clearly (extraction vs import vs export)
- Priorities become clearer (OCR accuracy vs audit compliance)
- Less confusion about requirements

## Migration Strategy

### **Phase 1: Documentation**
- ✅ Create this terminology guide
- ✅ Update ARCHITECTURE.md with clear terms
- Update issue descriptions to use consistent terminology

### **Phase 2: Code Comments**
```python
# Add clarifying comments to confusing functions
def import_review_selections():
    """Review OCR extraction results (not imports from external files)."""
```

### **Phase 3: Gradual Refactoring**
- Rename files and functions over multiple releases
- Maintain backwards compatibility
- Update CLI command names with aliases

The goal is **conceptual clarity** - users should immediately understand what each part of the system does without having to decode overloaded terminology.
