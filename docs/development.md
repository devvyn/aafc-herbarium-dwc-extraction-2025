# Development guide

## General guidelines

The [roadmap](roadmap.md) is the single source for open tasks, priorities, and timelines. Review it before starting work or filing a pull request to avoid duplication.

Run `./bootstrap.sh` before development to install dependencies, copy `.env.example`, and execute linting/tests.

- Keep preprocessing, OCR, mapping, QC, import, and export phases decoupled.
- Prefer configuration-driven behavior and avoid hard-coded values.
- Document new processing phases with reproducible examples.

## Testing and linting

Run the full test suite and linter before committing changes.

```bash
ruff check .
pytest
```

These checks help maintain a consistent code style and verify that new contributions do not introduce regressions.
