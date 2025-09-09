# Development guide

## Open stubs and placeholders

- [`qc/gbif.py`](../qc/gbif.py) defines endpoints and field maps but the
  `verify_taxonomy` and `verify_locality` methods raise `NotImplementedError`.
- [`dwc/schema.py`](../dwc/schema.py) hard-codes Darwin Core terms. Loading terms
  from a configured schema or XSD remains a future task.
- [`io_utils/database.py`](../io_utils/database.py) and
  [`io_utils/candidates.py`](../io_utils/candidates.py) use raw SQLite. An ORM
  such as SQLAlchemy could clarify data models and migrations.
- [`config/rules/dwc_rules.toml`](../config/rules/dwc_rules.toml) and
  [`config/rules/vocab.toml`](../config/rules/vocab.toml) now ship with starter
  mappings for common field aliases and controlled terms, but many Darwin Core
  fields—such as *habitat* or coordinate precision—and additional vocabulary
  values remain unmapped.

## Potential improvements

- Support alternative schemas via the `[dwc]` section in configuration and map
  URIs accordingly.
- Introduce an ORM layer for the pipeline database to improve readability and
  enable richer queries.
- Expand documentation for each processing phase with reproducible examples.
