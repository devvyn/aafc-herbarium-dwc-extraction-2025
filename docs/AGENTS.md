# AGENTS.md

## Documentation Guidelines
- Use Markdown with sentence-case headings.
- Organize content by workflow phase: preprocessing, OCR, mapping, QC, import, and export.
- Provide relative links to code or other docs instead of duplicating explanations.
- Highlight the separation between the digitization pipeline and the main DwC+ABCD database when relevant.
- Examples should be reproducible via repository scripts; do not paste hand-edited outputs.
- When features alter workflows or dependencies, refresh any affected usage or installation instructions (e.g., README.md and related docs).
- Reviewers should verify these documentation updates during PR review.
- Note any requirement to set `GITHUB_TOKEN` for scripts that call the GitHub API.

## Testing
- Run `ruff check docs` and `pytest` from the repository root before committing documentation changes.

## Issue Management
- Reference targeted GitHub issues with syntax like `#123` in commits and pull requests so they auto-link or close.
- When an issue affecting documentation is resolved or reopened, update any relevant docs accordingly.
- After closing an issue, review `roadmap.md` and TODO lists for follow-up ideas and open new issues for any additional suggestions or problems.
