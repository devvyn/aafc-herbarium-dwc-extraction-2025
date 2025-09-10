# AGENTS.md

## Darwin Core & ABCD Modules
- `schema.py` defines the canonical list of supported Darwin Core terms. Update it when adding new terms and keep ordering consistent.
- Add mapping logic in `mapper.py` and normalization rules in `normalize.py`; keep functions small and pure.
- When adding ABCD fields, provide a comment with the equivalent term and update validators accordingly.
- Expand unit tests to cover new terms or transformations.

## Testing
- After changes in this directory, run `ruff check dwc` and the project test suite (`pytest`) from the repository root.

## Issue Management
- Include GitHub issue numbers (e.g. `#123`) in commits and pull requests when work addresses a specific issue.
- Ensure any related documentation or mappings are updated if the linked issue is resolved or reopened.
- When closing an issue, consult `../docs/roadmap.md` and TODO lists for new recommendations and create issues for any follow-up ideas or problems.
