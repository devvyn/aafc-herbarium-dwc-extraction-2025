# AGENTS.md

## Documentation Guidelines
- Use Markdown with sentence-case headings.
- Organize content by workflow phase: preprocessing, OCR, mapping, QC, import, and export.
- Provide relative links to code or other docs instead of duplicating explanations.
- Highlight the separation between the digitization pipeline and the main DwC+ABCD database when relevant.
- Examples should be reproducible via repository scripts; do not paste hand-edited outputs.

## Testing
- Run `ruff .` and `pytest` from the repository root before committing documentation changes.
