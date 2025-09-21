# CLAUDE.md - Herbarium OCR to Darwin Core

## Project Overview
This is a scientific digitization toolkit for AAFC (Agriculture and Agri-Food Canada) herbarium specimens. The system processes specimen images through OCR engines, extracts taxonomic and geographical metadata, maps results to Darwin Core standard, and maintains quality control through versioned exports.

**Current Version**: 0.1.4 - Production-ready with adaptive thresholding, GBIF verification, Darwin Core mappings, and audit tracking.

## Claude Code Collaboration Guidelines

### Relationship to S3 Image Toolkit
This project uses a companion **S3 Image Dataset Kit** (separate repo) for cloud storage of ~2,885 herbarium specimen images. The S3 toolkit provides:
- Content-addressed image storage (SHA256-based keys)
- JSONL manifest with metadata (dimensions, file sizes, content types)
- Read-through cache for OCR processing workflows
- Immutable storage preventing corruption

### Architecture Understanding

**Core Workflow:**
```
Herbarium Images → S3 Storage → OCR Processing → Text Extraction → Darwin Core Mapping → Database → Export
```

**Key Components:**
1. **Input Processing**: Images from `./input/` (sourced from S3 cache)
2. **OCR Engines**: Tesseract, Apple Vision, PaddleOCR, GPT models
3. **Pipeline Database**: SQLite for progress tracking and deduplication
4. **Darwin Core Mapping**: Scientific specimen metadata standards
5. **Export Formats**: CSV, Excel, JSONL, DwC-A bundles

### Development Conventions

**Follow Existing Patterns:**
- **File Organization**: Input → Processing → SQLite → Output structure
- **Configuration**: Uses `.env` for secrets, `pyproject.toml` for dependencies
- **OCR Strategy**: Multiple engines with confidence scoring
- **Quality Control**: Versioned exports with audit trails
- **Standards Compliance**: Darwin Core and GBIF verification

**Coding Standards (from AGENTS.md):**
- **Linting**: Use Ruff for both checking and formatting
- **Testing**: Run `pytest` before commits
- **Type Hints**: Use where helpful for scientific data structures
- **Commits**: Small, focused changes with gitmoji prefixes
- **Documentation**: Keep `docs/roadmap.md` current

### Key File Locations

**Core Modules:**
- `src/dwc_aafc/` - Main package code
- `examples/AAFC-SRDC/meta.json` - Herbarium data conventions
- `docs/` - Documentation and roadmap
- `tests/` - Test suite

**Configuration:**
- `.env` - API keys and settings (copy from `.env.example`)
- `pyproject.toml` - Dependencies and project metadata
- `bootstrap.sh` - Setup script

**Data Flow:**
- `./input/` - Source images (typically cached from S3)
- `./output/` - Generated artifacts and exports
- Local SQLite - Progress tracking and intermediate results

### Working with Images

**S3 Integration:**
- Images are stored in companion S3 toolkit with content-addressed keys
- Use S3 cache client for reliable access during OCR processing
- SHA256 hashes ensure image integrity and deduplication

**OCR Processing:**
- Support multiple engines: Tesseract, Apple Vision, PaddleOCR, GPT
- Install engines as optional dependencies based on requirements
- Confidence scoring helps with quality assessment

### Data Standards

**Darwin Core Compliance:**
- Maps OCR results to standard specimen metadata fields
- Taxonomic names, collection dates, geographic coordinates
- Collector information and institutional codes

**GBIF Verification:**
- Validates taxonomic names against GBIF backbone
- Ensures specimens meet international standards
- Supports biodiversity data aggregation

### Testing and Quality

**Before Committing:**
```bash
ruff check . --fix          # Lint and format
pytest -q                   # Run test suite
ruff check docs             # Check documentation
```

**For Documentation Changes:**
- Verify examples are reproducible
- Update affected workflow instructions
- Check relative links and references

### Claude Code Specific Guidance

**When to Use This Project:**
- OCR improvements and new engine integrations
- Darwin Core mapping enhancements
- Export format additions (CSV, DwC-A, etc.)
- Quality control and validation features
- Database schema modifications
- Performance optimizations for large specimen sets

**Integration with S3 Toolkit:**
- Both projects work together in the digitization pipeline
- S3 toolkit handles image storage and caching
- This project handles OCR and scientific metadata extraction
- Coordinate changes that affect the image → OCR → database workflow

**Scientific Context:**
- Herbarium specimens are pressed plant samples for scientific study
- Darwin Core is the global standard for biodiversity data
- AAFC is Canada's federal agriculture department
- This supports national botanical research and conservation

### Common Tasks for Agents

1. **OCR Engine Integration**: Add new engines, tune confidence thresholds
2. **Field Mapping**: Enhance Darwin Core field extraction from OCR text
3. **Export Features**: New output formats or filtering capabilities
4. **Quality Control**: Validation rules and confidence scoring
5. **Performance**: Optimize for large specimen collections
6. **Documentation**: Keep workflow guides current with code changes

### Collaboration Notes

This project uses both AGENTS.md (Codex guidelines) and CLAUDE.md (Claude Code guidelines). When working across both platforms:
- Maintain consistency in coding standards
- Update documentation in both contexts
- Coordinate on architectural changes
- Share insights on OCR accuracy and scientific data quality

The combination provides robust herbarium digitization capabilities supporting botanical research, conservation, and global biodiversity databases.