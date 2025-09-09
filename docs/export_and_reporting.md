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
hash and timestamp. Provide the user via `--user`:

```bash
python import_review.py output/review_v1.2.0.zip output/candidates.db --schema-version 1.2.0 --user alice
```

Audit records are accessible with `fetch_import_audit` in
[`io_utils/database.py`](../io_utils/database.py).

## Darwin Core archive exports

Use the archive helpers to build Darwin Core files and bundle them with a
manifest. The manifest records the export timestamp, commit hash and any filter
criteria. When `compress=True`, provide a semantic version string so the bundle
is saved as `dwca_v<version>.zip` under `output/`.

```bash
python - <<'PY'
from pathlib import Path
from dwc.archive import create_archive

create_archive(Path("output"), compress=True, version="1.0.0")
PY
```

## Versioning guidelines

Tag every export with a semantic version. The accompanying `manifest.json` makes
it possible to reproduce the dataset by recording filters and the exact code
commit.
