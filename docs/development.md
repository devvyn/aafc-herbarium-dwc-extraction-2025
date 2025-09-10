# Development guide

## General guidelines

The [roadmap](roadmap.md) is the single source for open tasks, priorities, and timelines. Review it before starting work or filing a pull request to avoid duplication.

- Keep preprocessing, OCR, mapping, QC, import, and export phases decoupled.
- Prefer configuration-driven behavior and avoid hard-coded values.
- Document new processing phases with reproducible examples.

## Testing and linting

Run `ruff check .` and `pytest` from the project root to validate changes before committing.
