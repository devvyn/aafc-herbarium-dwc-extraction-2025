# Secondary roadmap issues

The following GitHub issue drafts capture the remaining roadmap work that did not yet have tracker entries. Each issue links back to the relevant roadmap item and documents the context, implementation ideas, and acceptance criteria so they can be opened directly on GitHub.

## Issue #159: GPU-accelerated Tesseract inference
- **Summary:** Investigate GPU-backed builds of Tesseract (e.g. via OpenCL or CUDA distributions) and expose an engine flag that enables accelerated inference when the environment supports it.
- **Implementation notes:**
  - Benchmark GPU-enabled Tesseract builds against the current CPU-only flow using representative specimen images.
  - Detect GPU availability in `cli.py`/engine loaders and document any dependencies or configuration toggles required to activate acceleration.
  - Ensure the preprocessing stage still emits compatible image formats for GPU builds.
- **Acceptance criteria:** A documented configuration switch selects GPU acceleration, benchmarks demonstrate measurable speedups, and fallback to CPU processing remains intact.

## Issue #160: Batch image resizing pipeline integration
- **Summary:** Promote the standalone batch resizing helper into a first-class preprocessing pipeline option so large inputs are normalized automatically before OCR.
- **Implementation notes:**
  - Add configuration wiring so `scripts/batch_resize.py` behaviour can be invoked from `cli.py process` runs.
  - Record resizing decisions in the pipeline database for auditability and reruns.
  - Provide updated documentation showing the end-to-end flow with the integrated resizing step.
- **Acceptance criteria:** Operators can enable batch resizing from configuration alone, resized dimensions persist in the SQLite store, and docs illustrate how to use the new option.

## Issue #161: Parse official DwC and ABCD schemas
- **Summary:** Import authoritative Darwin Core and ABCD XSDs so field and vocabulary definitions are derived programmatically instead of maintained manually.
- **Implementation notes:**
  - Fetch and cache upstream schema files inside the repository or during runtime with version checks.
  - Generate structured metadata (e.g. via dataclasses or JSON) describing elements, types, and constraints for downstream mapping helpers.
  - Verify the generated metadata against existing rule files to confirm coverage.
- **Acceptance criteria:** A reproducible process produces parsed schema metadata, unit tests validate the parser against sample fragments, and documentation explains how the metadata feeds mapping utilities.

## Issue #162: Auto-generate Darwin Core term mappings
- **Summary:** Use the parsed schema metadata to propose or build mapping templates that align custom OCR fields to Darwin Core terms with minimal manual edits.
- **Implementation notes:**
  - Extend the mapping engine to read schema-derived metadata and suggest default aliases.
  - Provide a CLI or script that outputs starter `dwc_rules.toml` content for new collections based on detected terms.
  - Offer guidance on reconciling generated mappings with existing configuration overrides.
- **Acceptance criteria:** Running the helper produces a draft mapping file tailored to supplied schema input, and reviewers can adapt the output with minimal manual intervention.

## Issue #163: Configuration-driven GBIF endpoints
- **Summary:** Move GBIF endpoint URLs and ancillary settings completely into configuration files so deployments can redirect traffic without code changes.
- **Implementation notes:**
  - Audit modules using GBIF URLs and route them through `[qc.gbif]` (or similar) configuration entries.
  - Add validation ensuring custom endpoints respond as expected before the QC pipeline runs.
  - Document environment-specific examples for staging versus production GBIF mirrors.
- **Acceptance criteria:** All GBIF HTTP calls read from configuration, misconfiguration is surfaced clearly to operators, and docs show how to customise the endpoints.

## Issue #164: Gazetteer-powered locality cross-checks
- **Summary:** Integrate a Gazetteer API (e.g. GeoNames or WHOSONFIRST) into QC so locality descriptions from OCR are validated against authoritative geographic data.
- **Implementation notes:**
  - Build a lightweight client that queries the chosen Gazetteer service with locality strings and coordinates.
  - Flag mismatches or ambiguous results in the QC output, similar to GBIF validation flags.
  - Allow operators to configure API credentials and rate limiting concerns.
- **Acceptance criteria:** Gazetteer lookups can be toggled via configuration, QC results show locality validation signals, and error handling covers offline or rate-limited scenarios.

## Issue #165: ORM-backed pipeline storage
- **Summary:** Replace raw SQLite access patterns with an ORM layer to improve maintainability and enable richer migrations for the pipeline database.
- **Implementation notes:**
  - Evaluate lightweight ORMs (e.g. SQLModel, SQLAlchemy) that suit SQLite and potential future backends.
  - Model existing tables (candidates, audit logs, manifests) with explicit schemas and migrations.
  - Update IO helpers to use the ORM abstractions while preserving current behaviour.
- **Acceptance criteria:** Database interactions go through the ORM, migrations cover existing schema evolution, and tests verify the transition without data loss.

## Issue #166: Import audit sign-off workflow
- **Summary:** Extend import tooling to require explicit user sign-off and capture a detailed audit trail before data enters the main DwC+ABCD store.
- **Implementation notes:**
  - Expand `import_review.py` to prompt for or accept sign-off metadata (user, timestamp, rationale).
  - Persist sign-off entries in the pipeline database with references to import bundles and commit hashes.
  - Surface audit records through CLI or reporting utilities for later review.
- **Acceptance criteria:** Every import records a signed audit entry, operators can retrieve audit history via CLI commands, and documentation explains compliance expectations.

## Issue #167: Spreadsheet pivot-table reporting
- **Summary:** Generate spreadsheet exports that include prebuilt pivot tables summarising specimen counts, determinations, and QC flags for curatorial review.
- **Implementation notes:**
  - Extend `io_utils/spreadsheets.py` to add pivot tables using an engine such as `openpyxl`.
  - Allow operators to choose predefined pivot layouts via configuration or CLI arguments.
  - Ensure generated workbooks remain compatible with existing review workflows.
- **Acceptance criteria:** Exported spreadsheets contain at least one useful pivot table, configuration toggles select which summaries to include, and reviewers confirm compatibility with Excel/LibreOffice.

## Issue #168: GPT prompt coverage harness
- **Summary:** Build automated checks that exercise GPT-based prompts against fixtures to prevent regressions as templates evolve.
- **Implementation notes:**
  - Assemble representative prompt/response fixtures for supported GPT workflows.
  - Implement a harness (potentially under `tests/`) that validates prompts still produce parseable outputs or match expected schemas.
  - Integrate the harness into CI and document how to refresh fixtures when prompts change.
- **Acceptance criteria:** The test suite includes coverage checks for GPT prompts, failures highlight mismatches clearly, and docs describe how to update fixtures responsibly.

## Issue #169: Expand procedural documentation examples
- **Summary:** Add step-by-step walkthroughs across preprocessing, OCR, mapping, QC, import, and export docs so new operators can replicate end-to-end runs.
- **Implementation notes:**
  - Identify documentation gaps and create reproducible examples aligned with repository scripts.
  - Cross-link examples to relevant configuration snippets and CLI commands.
  - Highlight human-in-the-loop checkpoints to reinforce pipeline separation principles.
- **Acceptance criteria:** Each workflow phase doc includes at least one procedural example, links reference runnable scripts, and reviewers report improved clarity when onboarding.
