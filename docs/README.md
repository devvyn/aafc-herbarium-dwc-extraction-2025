# AAFC Herbarium Dataset Documentation

This directory contains the GitHub Pages site for the dataset.

## Structure

```
docs/
├── index.md           - Landing page
├── _config.yml        - Jekyll configuration
├── PUBLISHING.md      - Release workflow documentation
├── data/              - Dataset files (served via GitHub Pages)
│   ├── occurrence.csv
│   ├── dwc-archive.zip
│   └── raw.jsonl
└── README.md          - This file
```

## Accessing the Site

**Live URL**: https://devvyn.github.io/aafc-herbarium-dwc-extraction-2025/

## Local Preview

```bash
# Install Jekyll
gem install bundler jekyll

# Serve locally
cd docs
jekyll serve

# Open http://localhost:4000
```

## Updating Content

1. Edit `index.md` for landing page content
2. Add new pages as `.md` files in `docs/`
3. Update `_config.yml` for site settings
4. Commit and push to main branch
5. GitHub Pages rebuilds automatically

## Data Files

Data files in `docs/data/` are accessible at:
- https://devvyn.github.io/aafc-herbarium-dwc-extraction-2025/data/occurrence.csv
- https://devvyn.github.io/aafc-herbarium-dwc-extraction-2025/data/dwc-archive.zip
- https://devvyn.github.io/aafc-herbarium-dwc-extraction-2025/data/raw.jsonl

**Note**: GitHub serves these files with proper MIME types and CORS headers for easy access.

## Publishing Workflow

See [PUBLISHING.md](PUBLISHING.md) for detailed instructions on:
- Creating GitHub Releases
- Uploading to S3
- Versioning strategy
- Automated publishing
