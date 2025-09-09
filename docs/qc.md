# Quality control review

QC verifies extracted candidates before they enter the main DwC+ABCD store. Review work occurs on an exported database so decisions remain isolated from production.

## Review cycle

1. **Export** candidates to a standalone bundle with `export_review.py`.
2. **Review** the bundle outside the main store using interactive or spreadsheet workflows. See [review workflow](./review_workflow.md) for details.
3. **Import** approved selections back into the working database with `import_review.py` before ingesting them into the central store.

Keep the review database separate from the primary DwC+ABCD database at all times.

## Interactive review

During the QC phase, confirm OCR candidates alongside the source image.

```bash
python review.py --tui path/to/candidates.db specimen.jpg
```

Use the arrow keys to highlight a candidate and press Enter to confirm. The chosen value is persisted through [`io_utils.candidates.record_decision`](../io_utils/candidates.py). If the terminal cannot display images, a text placeholder is shown instead.

## GBIF lookups

Taxonomy and locality checks can call the GBIF API. The endpoints are configurable through the `[qc.gbif]` section of `config.toml` so deployments can target mirrors or staging servers:

```toml
[qc.gbif]
species_match_endpoint = "https://api.gbif.org/v1/species/match"
reverse_geocode_endpoint = "https://api.gbif.org/v1/geocode/reverse"
```
