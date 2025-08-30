# Database Schema

The application uses a lightweight SQLite database to track extraction
progress and review outcomes. The schema consists of four core tables.

## specimens
Stores basic information about each specimen.

| column       | type | notes                  |
|--------------|------|------------------------|
| specimen_id  | TEXT | primary identifier     |
| image        | TEXT | path to specimen image |

## candidates
Holds raw values produced by OCR engines. Includes an `error` flag for
modules that fail to produce a reliable value.

| column     | type   | notes                          |
|------------|--------|--------------------------------|
| run_id     | TEXT   | identifier for the OCR run     |
| image      | TEXT   | image filename                 |
| value      | TEXT   | extracted text                 |
| engine     | TEXT   | OCR engine name                |
| confidence | REAL   | engine confidence score        |
| error      | INTEGER| 1 if engine flagged an error   |

## final_values
Represents the final selected value for each metadata field.

| column      | type   | notes                                  |
|-------------|--------|----------------------------------------|
| specimen_id | TEXT   | links back to `specimens`              |
| field       | TEXT   | metadata field name                    |
| value       | TEXT   | chosen value                           |
| module      | TEXT   | module that produced the value         |
| confidence  | REAL   | confidence for the chosen value        |
| error       | INTEGER| 1 if reviewers flagged an error        |
| decided_at  | TEXT   | ISO timestamp of selection             |

## processing_state
Tracks per-module processing state for each specimen.

| column      | type   | notes                                  |
|-------------|--------|----------------------------------------|
| specimen_id | TEXT   | specimen identifier                    |
| module      | TEXT   | module name                            |
| status      | TEXT   | e.g. `pending`, `done`, `failed`       |
| confidence  | REAL   | optional confidence from the module    |
| error       | INTEGER| 1 if the module reported an error      |
| updated_at  | TEXT   | ISO timestamp of last update           |

## Migrations
Run migrations using:

```python
from pathlib import Path
from io_utils.migrate import migrate_db

migrate_db(Path("candidates.db"))
```

This upgrades older databases with the new columns and tables.
