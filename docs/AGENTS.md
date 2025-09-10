# AGENTS.md

## Documentation Guidelines
- Use Markdown with sentence-case headings.
- Organize content by workflow phase: preprocessing, OCR, mapping, QC, import, and export.
- Provide relative links to code or other docs instead of duplicating explanations.
- Highlight the separation between the digitization pipeline and the main DwC+ABCD database when relevant.
- Examples should be reproducible via repository scripts; do not paste hand-edited outputs.
- When features alter workflows or dependencies, refresh any affected usage or installation instructions (e.g., README.md and related docs).
- Reviewers should verify these documentation updates during PR review.

## Testing
- Run `ruff check docs` and `pytest` from the repository root before committing documentation changes.
