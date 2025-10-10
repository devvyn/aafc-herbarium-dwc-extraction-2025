# Architecture Overview

## The Dual Nature of This System

This project embodies **two distinct but complementary paradigms** that emerged during development:

### 1. **The Extraction Layer**: Images → Data
**Original Vision**: A focused OCR pipeline for herbarium digitization
- **Input**: Specimen images (JPG/PNG files)
- **Process**: OCR via Apple Vision, GPT-4 Vision, or other engines
- **Output**: Structured text data (CSV, JSON)
- **Philosophy**: Images are the source of truth; data is extracted

### 2. **The Curation Layer**: Data → Standards
**Enterprise Requirements**: A robust data management platform
- **Input**: Extracted data (potentially from multiple sources)
- **Process**: Review, validation, audit trails, quality control
- **Output**: Darwin Core Archives, GBIF submissions
- **Philosophy**: Database is the source of truth; data has governance

## Why This Matters

The dual nature creates **conceptual friction** when these paradigms collide:

- **Terminology confusion**: "Import" suggests importing data, but we're extracting from images
- **Over-complexity**: Enterprise audit requirements for simple OCR tasks
- **Identity crisis**: Is this an OCR tool or a database application?

## Architectural Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
├─────────────────────────────────────────────────────────────┤
│  CLI Commands     │  Web Interface     │  Export Formats    │
│  • process        │  • review_web.py   │  • CSV             │
│  • export         │  • curator tools   │  • Darwin Core     │
│  • resume         │  • quality control │  • GBIF archives   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    CURATION LAYER                           │
├─────────────────────────────────────────────────────────────┤
│  Data Management  │  Quality Control   │  Standards         │
│  • Review workflow│  • Confidence      │  • Darwin Core     │
│  • Audit trails   │  • Validation      │  • ABCD schema     │
│  • Multi-source   │  • Error handling  │  • GBIF compliance │
│  Database: SQLite with specimens, final_values, audit tables │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    EXTRACTION LAYER                         │
├─────────────────────────────────────────────────────────────┤
│  OCR Engines      │  Preprocessing     │  Text Processing   │
│  • Apple Vision   │  • Image resize    │  • Field parsing   │
│  • GPT-4 Vision   │  • Enhancement     │  • Name extraction │
│  • Google Vision  │  • Format conv.    │  • Date parsing    │
│  Raw images (JPG/PNG) → Structured text → Candidate records   │
└─────────────────────────────────────────────────────────────┘
```

## Usage Modes

### **Quick Mode**: Simple OCR Extraction
Perfect for researchers who just need data from images:
```bash
# Direct: Images → CSV (no database)
python cli.py process --input photos/ --output results/
# Results: occurrence.csv, raw.jsonl
```

### **Research Mode**: Full Review Workflow
For projects requiring quality control:
```bash
# Extract with database tracking
python cli.py process --input photos/ --output results/
# Review extracted data
python review_web.py --db results/candidates.db --images photos/
# Export approved data
python cli.py export --output results/ --version 1.0
```

### **Production Mode**: Enterprise Compliance
For institutional deployment with audit requirements:
```bash
# Full pipeline with audit trails
python cli.py process --input photos/ --output results/ --audit-user "curator@institution"
# Import external data sources
python cli.py import --source external_data.csv --output results/
# Generate compliance reports
python cli.py audit --output reports/
```

## Key Design Principles

### **1. Separation of Concerns**
- **Extraction**: Focus on OCR accuracy and throughput
- **Curation**: Focus on data quality and standards compliance
- Each layer can be used independently

### **2. Progressive Enhancement**
- Start simple (images → CSV)
- Add complexity as needed (database, review, audit)
- Enterprise features don't complicate basic usage

### **3. Multiple Entry Points**
- **Image extraction**: Primary use case (specimens → OCR)
- **Data import**: Secondary use case (CSV → database)
- **Manual entry**: Supported but not primary

### **4. Clear Terminology**
- **"Extract"**: Getting data from images (OCR process)
- **"Import"**: Bringing external data into the system
- **"Ingest"**: General term for adding data (any source)
- **"Export"**: Creating standardized output formats

## When to Use Which Layer

### **Use Extraction Layer When:**
- You have herbarium images and need structured data
- Focus is on OCR accuracy and processing speed
- Output is CSV/JSON for immediate use
- No need for complex review workflows

### **Use Curation Layer When:**
- Multiple people need to review/edit data
- Institutional audit requirements exist
- Data comes from multiple sources (OCR + manual + imports)
- Long-term data management is required

### **Use Both Layers When:**
- Processing thousands of specimens
- Quality control is critical
- GBIF submission is the goal
- Multiple curators are involved

## Database Schema Philosophy

The database supports **data curation**, not just OCR tracking:

```sql
-- Extraction tracking (OCR process)
specimens: Records OCR jobs and their status
processing_state: Tracks extraction progress and errors

-- Data curation (review and governance)
final_values: Curator-approved data fields
import_audit: Tracks all data sources and sign-offs
```

This design allows:
- OCR results to be reviewed and corrected
- Manual data entry alongside OCR
- Multiple data sources in one project
- Full audit trails for compliance

## Technology Choices

### **SQLite for Database**
- **Pros**: Simple, portable, no server required
- **Cons**: Limited concurrent access
- **Alternative**: PostgreSQL for multi-user institutions

### **Apple Vision for OCR**
- **Pros**: 95% accuracy, zero cost on macOS
- **Cons**: macOS only
- **Fallbacks**: Cloud APIs (Google, Azure, GPT-4 Vision)

### **Darwin Core for Standards**
- **Pros**: Biodiversity standard, GBIF compatible
- **Cons**: Complex schema
- **Extensions**: ABCD for additional fields

## Common Pain Points

### **"Why is there a database for OCR?"**
The database enables:
- Progress tracking for large batches
- Review workflow for quality control
- Audit trails for institutional compliance
- Multiple data sources beyond just OCR

### **"The workflow seems overcomplicated"**
Use Quick Mode for simple needs:
```bash
python cli.py process --input photos/ --output results/
# Done. Check results/occurrence.csv
```

### **"Import vs Extract confusion"**
- **Extract**: OCR from images (primary workflow)
- **Import**: External CSV/spreadsheet data (secondary)
- Most users only need extraction

## Future Evolution

### **Toward Simplicity**
- Make Quick Mode the default
- Hide enterprise features unless explicitly enabled
- Clearer documentation for each usage mode

### **Toward Power**
- Enhanced review interfaces
- Better audit trail reporting
- Integration with institutional databases

The architecture supports both directions while maintaining clear conceptual boundaries.
