# Quick Start Guide for Successor

## What You're Inheriting
- **2,800 herbarium specimen photos** already captured and processed
- **Complete OCR toolkit** for extracting label text from specimen images
- **Review workflows** for correcting and validating extracted data
- **SharePoint integration** for institutional data handoff

## Day 1: Get Running
1. **Check the processed data**: Look in `output/occurrence.csv` for extracted specimen records
2. **Review flagged items**: Use web interface at `python review_web.py` to correct low-confidence results
3. **Export to SharePoint**: Run export scripts to transfer data to institutional systems

## Your Main Tasks
1. **Quality control**: Review OCR results and make corrections
2. **Photography**: Continue photographing remaining specimens (if any)
3. **Data entry**: Fill gaps in extracted information
4. **Institutional delivery**: Regular exports to SharePoint and institutional databases

## Key Commands
```bash
# Process new photos
python cli.py process --input photos/ --output results/

# Review and correct results
python review_web.py --db results/candidates.db --images photos/

# Export a versioned Darwin Core bundle
python cli.py export --output results/ --version 1.1.0

# Check processing status
sqlite3 results/app.db "SELECT status, COUNT(*) FROM processing_state GROUP BY status;"
```

## Where Everything Lives
- **Photos**: `input/` directory
- **Results**: `output/` directory
- **Spreadsheets**: Export to SharePoint via `output/*.csv`
- **Documentation**: `docs/` directory
- **Configuration**: `config/` directory

## When You Need Help
1. Check `docs/troubleshooting.md` for common issues
2. Review `docs/user_guide.md` for detailed workflows
3. Contact information in `HANDOVER_PRIORITIES.md`

## Network Setup
- **On herbarium network**: Full access to SharePoint and email
- **Offline**: Can still process photos and generate spreadsheets
- **Sync later**: Upload results when back on network

---
**Start here**: Process the 2,800 existing photos first, then continue with any remaining specimens.
