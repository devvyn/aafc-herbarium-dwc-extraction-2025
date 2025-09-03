# Roadmap

Upcoming features and priorities for the herbarium OCR to Darwin Core toolkit.

## Preprocessing

| Feature | Priority | Timeline |
| --- | --- | --- |
| Add adaptive thresholding step in the [preprocessing flows](preprocessing_flows.md) | Medium | Q2 2025 |
| Batch resize large images to accelerate OCR | Low | Q3 2025 |

## OCR

| Feature | Priority | Timeline |
| --- | --- | --- |
| Integrate multilingual OCR models for non-English labels | High | Q2 2025 |
| Support GPU-accelerated inference for Tesseract | Medium | Q3 2025 |

## Mapping

| Feature | Priority | Timeline |
| --- | --- | --- |
| Configurable mapping from custom schemas via the [`[dwc]` section](configuration.md) | High | Q2 2025 |
| Auto-generate Darwin Core term mappings from external XSD | Low | Q4 2025 |

## QC

| Feature | Priority | Timeline |
| --- | --- | --- |
| Hook into [qc/gbif.py](../qc/gbif.py) for taxonomy validation | Medium | Q3 2025 |
| Implement locality cross-checks using Gazetteer API | Low | Q4 2025 |

## Import

| Feature | Priority | Timeline |
| --- | --- | --- |
| Audit trail for import steps with explicit user sign-off to keep pipeline and database separate | Medium | Q3 2025 |

## Export

| Feature | Priority | Timeline |
| --- | --- | --- |
| Versioned DwC-A export bundles with embedded manifest | High | Q2 2025 |
| Spreadsheet pivot table exports for data summaries | Low | Q4 2025 |

