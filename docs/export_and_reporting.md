# Export and reporting

Exports operate on the pipeline's SQLite database and never touch the main DwC+ABCD store.

## CSV exports

1. Run [`cli.py`](../cli.py) to process images and populate the local database. The
   `--input`, `--output`, `--config` and repeatable `--engine` options control the run.

   ```bash
   python cli.py process --input input/ --output output/ --config config/local.toml --engine tesseract
   ```

2. The command writes `occurrence.csv` and `identification_history.csv` in the
   `output/` directory. Inspect the files with standard tools:

   ```bash
   head output/occurrence.csv
   ```

## Excel exports

1. Convert the review database to a spreadsheet using
   [`io_utils/spreadsheets.py`](../io_utils/spreadsheets.py):

   ```bash
   python - <<'PY'
   from pathlib import Path
   from io_utils.database import init_candidate_db
   from io_utils.spreadsheets import export_candidates_to_spreadsheet

   conn = init_candidate_db(Path("output/candidates.db"))
   export_candidates_to_spreadsheet(conn, "1.0.0", Path("output/review.xlsx"))
   conn.close()
   PY
   ```

2. The spreadsheet and a `manifest.json` appear under `output/` for review
   without modifying the central database.

## Import audits

Use [import_review.py](../import_review.py) to merge reviewed decisions into the
working database. The command records an audit entry with the user ID, bundle
hash and timestamp. Audits are written to `app.db` next to the candidates file
unless an explicit path is provided via `--app-db`.

```bash
python import_review.py output/review_v1.2.0.zip output/candidates.db --schema-version 1.2.0 --user alice --app-db output/app.db
```

Audit records are accessible with `fetch_import_audit` in
[`io_utils/database.py`](../io_utils/database.py).

## Darwin Core archive exports

The system provides comprehensive Darwin Core Archive (DwC-A) export functionality with semantic versioning, embedded manifests, and rich provenance tracking.

### Quick Export via CLI

The easiest way to create versioned exports is through the CLI:

```bash
# Create a rich versioned bundle with full metadata
python cli.py export --output output/ --version 1.2.0 --format rich

# Create a simple versioned bundle
python cli.py export --output output/ --version 1.2.0 --format simple

# Export without compression (files only)
python cli.py export --output output/ --version 1.2.0 --no-compress
```

### Programmatic Export

Use the archive helpers to build Darwin Core files and bundle them with enhanced manifests:

```bash
python - <<'PY'
from pathlib import Path
from dwc.archive import create_archive, create_versioned_bundle

# Simple versioned bundle
create_archive(Path("output"), compress=True, version="1.0.0")

# Rich bundle with enhanced metadata
create_versioned_bundle(
    Path("output"),
    version="1.2.0",
    bundle_format="rich",
    include_checksums=True,
    additional_files=["processing_log.txt"]
)
PY
```

### Bundle Formats

Two bundle formats are available:

**Rich Format** (default): `dwca_v1.2.0_20241201T120000Z_abc1234_ef567890.zip`
- Includes version, timestamp, git commit hash, and filter hash
- Full provenance tracking
- Recommended for archival and reproducibility

**Simple Format**: `dwca_v1.2.0.zip`
- Clean, version-only filename
- Suitable for regular distribution

### Enhanced Manifest Features

The embedded `manifest.json` now includes:

- **Format versioning**: Schema version for the manifest format itself
- **Git information**: Commit hash, branch, dirty status detection
- **System information**: Platform, Python version, package version
- **File checksums**: SHA256 hashes and file sizes for integrity verification
- **Export metadata**: Timestamp, version, filters, bundle format

Example manifest structure:

```json
{
  "format_version": "1.1.0",
  "export_type": "darwin_core_archive",
  "timestamp": "2024-12-01T12:00:00.000000+00:00",
  "version": "1.2.0",
  "bundle_format": "rich",
  "git_commit": "abc1234567890def",
  "git_commit_short": "abc1234",
  "git_branch": "main",
  "git_dirty": false,
  "filters": {},
  "system_info": {
    "platform": "Darwin-24.6.0-arm64",
    "python_version": "3.11.5",
    "python_executable": "/usr/bin/python3"
  },
  "file_checksums": {
    "occurrence.csv": {
      "sha256": "e3b0c44298fc1c149afbf4c8996fb924...",
      "size_bytes": 1024
    },
    "identification_history.csv": {
      "sha256": "d4f5e6789abc123def456789...",
      "size_bytes": 512
    },
    "meta.xml": {
      "sha256": "a1b2c3d4e5f6789012345678...",
      "size_bytes": 2048
    }
  }
}
```

### Configuration Options

Configure export behavior in your `config.toml` file:

```toml
[export]
enable_versioned_exports = true
default_export_version = "1.0.0"
bundle_format = "rich"  # "rich" or "simple"
include_checksums = true
include_git_info = true
include_system_info = true
export_retention_days = 365
additional_files = ["README.txt", "processing_log.txt"]
```

### Versioning Guidelines

- **MAJOR.MINOR.PATCH** semantic versioning is required
- Tag every export with a meaningful version
- Use MAJOR for breaking schema changes
- Use MINOR for new fields or features
- Use PATCH for data corrections or updates
- The `manifest.json` ensures complete reproducibility

### Archive Validation

Validate DwC-A bundles using standard tools:

```bash
# Check archive contents
unzip -l dwca_v1.2.0.zip

# Verify checksums
python -c "
import zipfile, json, hashlib
with zipfile.ZipFile('dwca_v1.2.0.zip') as zf:
    manifest = json.loads(zf.read('manifest.json'))
    for filename, info in manifest['file_checksums'].items():
        content = zf.read(filename)
        actual = hashlib.sha256(content).hexdigest()
        expected = info['sha256']
        print(f'{filename}: {\'✓\' if actual == expected else \'✗\'}')
"
```

### Integration with GBIF and DataONE

The enhanced DwC-A format is fully compatible with:
- **GBIF IPT**: Direct upload of versioned archives
- **DataONE**: Rich metadata supports data package requirements
- **BiodiversityLinks**: Embedded provenance aids citation tracking
- **Darwin Core standard**: Compliant meta.xml and CSV structure

### Export Retention

Configure automatic cleanup of old exports:

```bash
# Clean exports older than retention period
python - <<'PY'
from pathlib import Path
import time
from datetime import datetime, timedelta

output_dir = Path("output")
retention_days = 365  # From config
cutoff = datetime.now() - timedelta(days=retention_days)

for archive in output_dir.glob("dwca_*.zip"):
    if archive.stat().st_mtime < cutoff.timestamp():
        print(f"Removing old export: {archive.name}")
        archive.unlink()
PY
```

## Recent Enhancements

✅ **Issue #158 Complete**: Versioned DwC-A export bundles with embedded manifests
- Enhanced semantic versioning with rich provenance tags
- Comprehensive manifest embedding with checksums and system info
- CLI integration for easy export workflows
- Configuration-driven export behavior
- Full Darwin Core Archive standard compliance
