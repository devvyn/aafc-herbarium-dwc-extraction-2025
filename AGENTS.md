# AGENTS.md

## Data & Folder Conventions
- **Fields:** refer to `examples/AAFC-SRDC/meta.json` for herbarium data conventions.
- **Input:** place source images or other inbound data under `./input/`; nested subdirectories allowed.
- **Output:** write all generated artifacts to `./output/`.
- **Database:** use a lightweight SQLite database to track progress, deduplicate work, and resume runs.
- **Exports:** generate CSV, spreadsheet, or DwC-A files from the intermediate database—never parse existing output files.

## Digitization Workflow & Separation
- Run preprocessing, OCR, candidate extraction, and refinement outside the central DwC+ABCD store.
- The main database only ingests curated values; keep raw artifacts and provenance (image hash, OCR engine, confidence) in the pipeline's SQLite store.
- Treat imports as an explicit, auditable step with no hidden side effects.

## Export Versioning
- Support export formats: filtered CSV, Excel, pivot tables, JSONL, and zipped DwC-A bundles.
- Tag each export with timestamp, filter criteria, and commit hash to ensure reproducibility.
- Store exported artifacts under `./output/` with semantic version tags.

## Coding Style & Tooling
- Use **Ruff** for both linting and formatting.
  - Auto-fix: `ruff check . --fix`
- Follow standard Python idioms (PEP 8, type hints where helpful).

## Testing
- Run tests before committing (e.g., `pytest`).
- Optionally run any DWCA validator scripts if they exist.

## Commit & PR Guidelines
- Keep commits **small and focused**; each commit should address one logical change.
- Write clear commit messages that explain the intent of the change.
- Start commit messages with a gitmoji (see [gitmoji.dev](https://gitmoji.dev)) followed by a short summary.
- All updates to `CHANGELOG.md` must follow the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.
- Use GitHub-style links for issues, commits, and pull requests (e.g. `[PR #42](https://github.com/your-org/your-repo/pull/42)`).
- Open pull requests only after all linting/tests pass.

## Release Guidelines
- Publish a release only for **substantial** changes that add features, fix user-facing bugs, or alter data structures.
- Every release must synchronize version numbers and update both `CHANGELOG.md` and `README.md`.
- Skip releases for minor internal tweaks, refactors, or other changes with no external impact.

## Documentation & roadmap
- Keep `docs/roadmap.md` current; update it whenever project scope or priorities change.
- Pull requests touching areas with open tasks must reconcile or reference the relevant entries in `docs/roadmap.md`.
- Default to tasks in `docs/roadmap.md` when no explicit direction is given and create minimal stubs or scaffolding for them.
- Pair each stubbed task with brief documentation so future iterations have clear context.

## Human-in-the-loop Generative Development
- Break work into small, reviewable steps and solicit feedback early.
- Record assumptions, open questions, and decisions in code comments or documentation.
- Iterate with human reviewers to refine generative outputs and documentation.

## Miscellaneous
- No sensitive data is handled in this repository.
- Default image format is JPEG unless otherwise specified.
- Set `GITHUB_TOKEN` before running scripts that interact with the GitHub API.
