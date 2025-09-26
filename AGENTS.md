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
- When a pull request is meant to close an issue, include a closing keyword such as `Resolves #<issue-number>` in the PR description.
- Open pull requests only after all linting/tests pass.

## Issue Management
- Tasks targeting a GitHub issue must reference the issue number using GitHub syntax (e.g. `#123`) in commits and pull requests to enable auto-linking or closing.
- When an issue is resolved or reopened, ensure any related documents (such as `docs/roadmap.md`) are updated.
- After closing an issue, review `docs/roadmap.md` and existing TODOs for follow-up ideas and file new issues for additional suggestions or problems.

## Release Guidelines
- Publish a release only for **substantial** changes that add features, fix user-facing bugs, or alter data structures.
- Every release must synchronize version numbers and update both `CHANGELOG.md` and `README.md`.
- Skip releases for minor internal tweaks, refactors, or other changes with no external impact.

### Complete Release Process
When creating a release, **all steps must be completed** to prevent broken CHANGELOG links:

1. **Update version numbers** in:
   - `pyproject.toml` (version field)
   - `README.md` (current version description)
   - `CHANGELOG.md` (new version section with date)

2. **Create git tag immediately after release commit**:
   ```bash
   git tag v<version> <commit-sha>
   git push origin --tags
   ```

3. **Verify CHANGELOG links work**:
   - CHANGELOG.md comparison links require actual git tags to function
   - Test links like `[0.2.0]: https://github.com/owner/repo/compare/v0.1.4...v0.2.0`
   - If tags are missing, comparison pages return 404 errors

4. **Follow semantic versioning**: v0.1.0, v0.2.0, v1.0.0, etc.

**Critical**: Never update CHANGELOG.md version references without creating corresponding git tags. This breaks the Keep a Changelog format and creates non-functional comparison links.

## Documentation & roadmap
- Keep `docs/roadmap.md` current; update it whenever project scope or priorities change.
- Pull requests touching areas with open tasks must reconcile or reference the relevant entries in `docs/roadmap.md`.
- Default to tasks in `docs/roadmap.md` when no explicit direction is given and create minimal stubs or scaffolding for them.
- Pair each stubbed task with brief documentation so future iterations have clear context.

## Human-in-the-loop Generative Development
- Break work into small, reviewable steps and solicit feedback early.
- Record assumptions, open questions, and decisions in code comments or documentation.
- Iterate with human reviewers to refine generative outputs and documentation.

## Pair Programming Partnership (Encouraged)
- **Act as active programming partner**, not just code generator
- **Question assumptions**: "Are we solving the real problem or just the technical problem?"
- **Balance high-level vs hands-on**: "When did you last test this on actual data?"
- **Keep sight of end goals**: "Will this help the actual user accomplish their task?"
- **Flag disconnects**: "The code works, but does it work for the real workflow?"
- **Propose next steps**: Suggest practical testing and validation approaches
- **Create human work lists**: Identify tasks that require human expertise or access
- **Bridge theory-practice gaps**: Ensure solutions work in real institutional environments

## Miscellaneous
- No sensitive data is handled in this repository.
- Default image format is JPEG unless otherwise specified.
- Set `GITHUB_TOKEN` before running scripts that interact with the GitHub API.

## AI Assistant Operating Notes
- Audit the repository for additional `AGENTS.md` files before modifying any code or documentation so that the most specific
  instructions are always applied. More specific directories (e.g., `./dwc/AGENTS.md`) override parent directories when both exist.
- Prefer incremental, reviewable changes: stage only the files that are necessary for the current task and avoid sweeping
  refactors without prior coordination. This aligns with the "Human-in-the-loop Generative Development" approach above.
- Record tooling or workflow limitations (e.g., unavailable browsers or external services) in pull request descriptions and
  final status reports so reviewers understand any gaps in validation.

  Example format:
  ```
  ## Limitations Encountered
  - Unable to run browser tests: Headless browser not available in CI environment
  - Skipped API integration test: External service requires credentials not present
  ```
- When environment constraints prevent running an expected command, document the limitation and provide suggested follow-up
  actions for human collaborators. If constraints cannot be resolved with available tools, escalate to human reviewers with
  clear context about what was attempted and what remains to be done.
