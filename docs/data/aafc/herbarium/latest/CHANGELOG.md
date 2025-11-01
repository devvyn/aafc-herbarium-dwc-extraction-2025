# Data Changelog (Latest/Continuous)

This directory contains the **latest unreleased data** from the main branch.

**⚠️ WARNING**: This is bleeding-edge data. It may change at any time without notice.

## Current Build

- **Timestamp**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
- **Commit**: 4581148740fb89e157e31c81e36ce52e4cf853bd
- **Workflow**: 1

## Stability Levels

| Location | Stability | Use Case |
|----------|-----------|----------|
| `/data-latest/` | ⚠️ Unstable | Live development, testing updates |
| `/data/` | 🧪 Preview | Versioned snapshots (via Releases) |
| GitHub Releases | ✅ Stable | Production use, citations |

## Files in This Directory

- `occurrence.csv` - Latest Darwin Core CSV
- `dwc-archive.zip` - Latest GBIF archive
- `raw.jsonl` - Latest raw extractions with confidence
- `metadata.json` - Build metadata
- `CHANGELOG.md` - This file

## Update Frequency

**Automatic**: Every push to main branch that modifies data files
**Manual**: Via workflow_dispatch

## Usage

```bash
# Download latest CSV
wget https://devvyn.github.io/aafc-herbarium-dwc-extraction-2025/data-latest/occurrence.csv

# Check when it was built
curl https://devvyn.github.io/aafc-herbarium-dwc-extraction-2025/data-latest/metadata.json
```

## Tracking Changes

To track incremental changes:

```bash
# Set up daily sync
0 */6 * * * wget -N https://devvyn.github.io/.../data-latest/occurrence.csv

# Compare with previous version
diff old_occurrence.csv occurrence.csv > changes.diff
```

## Migration to Stable Release

When data quality is verified, it gets promoted:

1. Latest (continuous) → Tested internally
2. Preview release → Shared for review
3. Stable release → Tagged and archived

---

*Last updated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")*
