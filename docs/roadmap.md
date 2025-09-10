# Roadmap

Upcoming features and priorities for the herbarium OCR to Darwin Core toolkit.

Run `python scripts/create_roadmap_issues.py --repo <owner>/<repo>` to open GitHub issues for tasks marked with `(Issue TBD)`.

**Critical features**
- Integrate multilingual OCR models for non-English labels
- Integrate GBIF taxonomy and locality verification into the QC pipeline
- Configurable mapping from custom schemas via the [`[dwc]` section](configuration.md)
- Versioned DwC-A export bundles with embedded manifest
- Populate mapping rules in `config/rules/dwc_rules.toml` and `config/rules/vocab.toml`

Secondary tasks cover medium and low priority items detailed below.

## Preprocessing and OCR

- Integrate multilingual OCR models for non-English labels — **High**, Q2 2025 (https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/138)
- Support GPU-accelerated inference for Tesseract — **Medium**, Q3 2025
- Batch resize large images to accelerate OCR — **Low**, Q3 2025

## Mapping and vocabulary

- Configurable mapping from custom schemas via the [`[dwc]` section](configuration.md) — **High**, Q2 2025
- Populate mapping rules in `config/rules/dwc_rules.toml` and `config/rules/vocab.toml` — **High**, Q2 2025
- Support full schema parsing from official Darwin Core and ABCD XSDs — **Medium**, Q3 2025
- Auto-generate Darwin Core term mappings from external XSD — **Low**, Q4 2025

## Quality control

- Integrate GBIF taxonomy and locality verification into the QC pipeline — **Medium**, Q3 2025 (https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025/issues/139)
- Move GBIF API endpoints into configuration files — **Low**, Q2 2025
- Implement locality cross-checks using Gazetteer API — **Low**, Q4 2025

## Database and import

- Transition pipeline storage to an ORM — **Medium**, Q3 2025
- Audit trail for import steps with explicit user sign-off to keep pipeline and database separate — **Medium**, Q3 2025

## Export and reporting

- Versioned DwC-A export bundles with embedded manifest — **High**, Q2 2025
- Spreadsheet pivot table exports for data summaries — **Low**, Q4 2025

## Testing and documentation

- Add evaluation harness for GPT prompt template coverage — **Medium**, Q2 2025 (see `scripts/prompt_coverage.py`)
- Expand procedural examples across docs — **Low**, Q3 2025
