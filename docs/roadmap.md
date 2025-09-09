# Roadmap

Upcoming features and priorities for the herbarium OCR to Darwin Core toolkit.

**Critical features**
- Integrate multilingual OCR models for non-English labels
- Configurable mapping from custom schemas via the [`[dwc]` section](configuration.md)
- Versioned DwC-A export bundles with embedded manifest

Secondary tasks cover medium and low priority items detailed below.

## Preprocessing and OCR

| Feature | Priority | Timeline |
| --- | --- | --- |
| Batch resize large images to accelerate OCR | Low | Q3 2025 |
| Integrate multilingual OCR models for non-English labels | High | Q2 2025 |
| Support GPU-accelerated inference for Tesseract | Medium | Q3 2025 |

## Mapping and vocabulary

| Feature | Priority | Timeline |
| --- | --- | --- |
| Configurable mapping from custom schemas via the [`[dwc]` section](configuration.md) | High | Q2 2025 |
| Populate mapping rules in `config/rules/dwc_rules.toml` and `config/rules/vocab.toml` | Medium | Q2 2025 |
| Auto-generate Darwin Core term mappings from external XSD | Low | Q4 2025 |

## Quality control

| Feature | Priority | Timeline |
| --- | --- | --- |
| Hook into [qc/gbif.py](../qc/gbif.py) for taxonomy validation | Medium | Q3 2025 |
| Move GBIF API endpoints into configuration files | Low | Q2 2025 |
| Implement locality cross-checks using Gazetteer API | Low | Q4 2025 |

## Database and import

| Feature | Priority | Timeline |
| --- | --- | --- |
| Transition pipeline storage to an ORM | Medium | Q3 2025 |
| Audit trail for import steps with explicit user sign-off to keep pipeline and database separate | Medium | Q3 2025 |

## Export and reporting

| Feature | Priority | Timeline |
| --- | --- | --- |
| Versioned DwC-A export bundles with embedded manifest | High | Q2 2025 |
| Spreadsheet pivot table exports for data summaries | Low | Q4 2025 |

## Testing and documentation

| Feature | Priority | Timeline |
| --- | --- | --- |
| Add tests covering configurable GPT prompt templates | Medium | Q2 2025 |
| Expand procedural examples across docs | Low | Q3 2025 |
