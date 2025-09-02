# Review workflow

## Export
Use [export_review.py](../export_review.py) to package images, `candidates.db`, and a JSON manifest. The script writes bundles such as `review_v1.2.0.zip` to `output/` and records the current commit hash and schema version.

## Transfer
Upload the bundle to SharePoint or attach it to an email for manual review. Keep the file intact so the manifest, images, and database remain synchronized.

## Import
When decisions are returned, run [import_review.py](../import_review.py) with the expected schema version. The script validates the commit hash and prevents duplicate decision records before merging updates into the local database.
