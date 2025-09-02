# Review workflow

Export candidates to a self-contained bundle, review selections outside the main DwC+ABCD database, then import the decisions.

## Export bundle

Use [export_review.py](../export_review.py) to package `candidates.db`, images, and a manifest into `output/review_vX.Y.Z.zip`.

```
python export_review.py output/candidates.db input/images --schema-version 1.2.0
```

## TUI review

Launch the text-based interface via [review.py](../review.py) with the `--tui` flag. Decisions are written back to the exported database, keeping review separate from the central store.

- **Windows**

  ```
  py review.py --tui output/candidates.db image.jpg
  ```

- **macOS/Linux**

  ```
  python3 review.py --tui output/candidates.db image.jpg
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

```python
import sqlite3
from pathlib import Path

from io_utils.candidates import Candidate, record_decision
from io_utils.spreadsheets import (
    export_candidates_to_spreadsheet,
    import_review_selections,
)

conn = sqlite3.connect("output/candidates.db")
export_candidates_to_spreadsheet(conn, "1.2.0", Path("output/review.xlsx"))

# After reviewers mark the 'selected' column
for d in import_review_selections(Path("output/review.xlsx"), "1.2.0"):
    record_decision(conn, d["image"], Candidate(d["value"], d["engine"], 1.0))
```

## Import decisions

Merge reviewed selections back into your working database with [import_review.py](../import_review.py):

```
python import_review.py output/review_v1.2.0.zip output/candidates.db --schema-version 1.2.0
```

