# Review workflow

## Export
Use [export_review.py](../export_review.py) to package images, `candidates.db`, and a JSON manifest. The script writes bundles such as `review_v1.2.0.zip` to `output/` and records the current commit hash and schema version.

## Transfer
Upload the bundle to SharePoint or attach it to an email for manual review. Keep the file intact so the manifest, images, and database remain synchronized.

## Spreadsheet review
Use [io_utils/spreadsheets.py](../io_utils/spreadsheets.py) to export candidate rows to an Excel file:

```python
from io_utils.spreadsheets import export_candidates_to_spreadsheet

export_candidates_to_spreadsheet(conn, "1.0.0", Path("output/review.xlsx"))
```

Upload the `.xlsx` file to SharePoint for reviewers. They mark the `selected` column for accepted values. After collaboration, download the file and import decisions:

```python
from io_utils.spreadsheets import import_review_selections

decisions = import_review_selections(Path("output/review.xlsx"), "1.0.0")
```

The import step validates the manifest's commit hash and schema version before returning selections for ingestion.

## Import
When decisions are returned, run [import_review.py](../import_review.py) with the expected schema version. The script validates the commit hash and prevents duplicate decision records before merging updates into the local database.
