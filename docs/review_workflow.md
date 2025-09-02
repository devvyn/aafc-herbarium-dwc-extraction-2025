# Review workflow

Export candidates to a self-contained bundle, review selections outside the main DwC+ABCD database, then import the decisions.

## Export bundle

Use [export_review.py](../export_review.py) to package `candidates.db`, images, and a manifest into `output/review_vX.Y.Z.zip`.

```
python export_review.py --output output/review_v1.2.0.zip
```

## TUI review

The [review_tui.py](../review_tui.py) script provides a text-based interface using the exported SQLite database. Selections are written back to the same database, keeping review separate from the central store.

- **Windows**

  ```
  py review_tui.py output/candidates.db image.jpg
  ```

- **macOS/Linux**

  ```
  python3 review_tui.py output/candidates.db image.jpg
  ```

## Web UI review

Run [review_web.py](../review_web.py) to review candidates in a browser. Decisions update the exported `candidates.db` without touching the main database.

- **Windows**

  ```
  py review_web.py --db output/candidates.db --images output
  ```

- **macOS/Linux**

  ```
  python3 review_web.py --db output/candidates.db --images output
  ```

Visit `http://localhost:8000` to start reviewing.

## Spreadsheet-based review

Use [io_utils/spreadsheets.py](../io_utils/spreadsheets.py) for teams that prefer spreadsheets.

Export candidates:

- **Windows**

  ```
  py -m io_utils.spreadsheets export output/candidates.db output/review.xlsx
  ```

- **macOS/Linux**

  ```
  python3 -m io_utils.spreadsheets export output/candidates.db output/review.xlsx
  ```

After reviewers mark the `selected` column, import the decisions:

- **Windows**

  ```
  py -m io_utils.spreadsheets import output/review.xlsx output/candidates.db
  ```

- **macOS/Linux**

  ```
  python3 -m io_utils.spreadsheets import output/review.xlsx output/candidates.db
  ```

## Import decisions

Merge reviewed selections back into your working database with [import_review.py](../import_review.py):

```
python import_review.py output/review_v1.2.0.zip
```

