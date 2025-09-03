# Review workflow

Export candidates to a self-contained bundle, review selections outside the main DwC+ABCD database, then import the decisions.

## Export bundle

Use [export_review.py](../export_review.py) to package `candidates.db`, images, and a manifest into `output/review_vX.Y.Z.zip`.

```
python export_review.py output/candidates.db input --schema-version 1.2.0
```

## TUI review

Launch the text-based interface with `python review.py output/candidates.db image.jpg --tui`. Selections are written back to the same database, keeping review separate from the central store.

- **Windows**

  ```
  py review.py output/candidates.db image.jpg --tui
  ```

- **macOS/Linux**

  ```
  python3 review.py output/candidates.db image.jpg --tui
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

Use [io_utils/spreadsheets.py](../io_utils/spreadsheets.py) helper functions for teams that prefer spreadsheets.

Export candidates:

```python
from pathlib import Path
import sqlite3
from io_utils.spreadsheets import export_candidates_to_spreadsheet

with sqlite3.connect("output/candidates.db") as conn:
    export_candidates_to_spreadsheet(conn, "1.2.0", Path("output/review.xlsx"))
```

After reviewers mark the `selected` column, import the decisions:

```python
from pathlib import Path
import sqlite3
from io_utils.candidates import Candidate, record_decision
from io_utils.spreadsheets import import_review_selections

with sqlite3.connect("output/candidates.db") as conn:
    for d in import_review_selections(Path("output/review.xlsx"), "1.2.0"):
        cand = Candidate(value=d["value"], engine=d["engine"], confidence=0.0)
        record_decision(conn, d["image"], cand)
```

## Import decisions

Merge reviewed selections back into your working database with [import_review.py](../import_review.py):

```
python import_review.py output/review_v1.2.0.zip output/candidates.db --schema-version 1.2.0
```

