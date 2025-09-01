# Review workflow

## Preprocessing
Place source images under `input/` before running OCR.

## OCR
Run the extraction pipeline to populate [candidates.db](../io_utils/candidates.py) with OCR outputs.

## QC
Start the lightweight web reviewer to confirm candidate values alongside their images:

```bash
python review_web.py --db candidates.db --images input/
```

Selections are written to a SQLite database separate from the main DwC+ABCD store.

## Import
Review decisions must be imported explicitly into the primary database.

## Export
Exports should embed the commit hash and export version for reproducibility. See [review_web.py](../review_web.py) for details.
