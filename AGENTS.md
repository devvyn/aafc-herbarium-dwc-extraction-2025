# AGENTS.md

## Data & Folder Conventions
- **Fields:** refer to 'examples/AAFC-SRDC/meta.json' for herbarium data conventions.
- **Input:** place source images or other inbound data under `./input/`; nested subdirectories allowed.
- **Output:** write all generated artifacts to `./output/`.
- **Database:** use a lightweight SQLite database to track progress, deduplicate work, and resume runs.
- **Exports:** when creating CSV or spreadsheet files, generate them from the intermediate database—never parse existing output files.

## Coding Style & Tooling
- Use **Ruff** for both linting and formatting.
  - Auto-fix: `ruff --fix .`
  - Lint without fixing: `ruff .`
- Follow standard Python idioms (PEP 8, type hints where helpful).

## Testing
- Run tests before committing (e.g., `pytest`).
- Optionally run any DWCA validator scripts if they exist.

## Commit & PR Guidelines
- Keep commits **small and focused**; each commit should address one logical change.
- Write clear commit messages that explain the intent of the change.
- Open pull requests only after all linting/tests pass.

## Miscellaneous
- No sensitive data is handled in this repository.
- Default image format is JPEG unless otherwise specified.
