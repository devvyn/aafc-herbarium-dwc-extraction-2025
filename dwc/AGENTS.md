# AGENTS.md

## Darwin Core & ABCD Modules
- `schema.py` defines the canonical list of supported Darwin Core terms. Update it when adding new terms and keep ordering consistent.
- Add mapping logic in `mapper.py` and normalization rules in `normalize.py`; keep functions small and pure.
- When adding ABCD fields, provide a comment with the equivalent term and update validators accordingly.
- Expand unit tests to cover new terms or transformations.

## Testing
- After changes in this directory, run `uv format dwc` and the project test suite via `uv run pytest` from the repository root.
