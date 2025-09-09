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

When enabled, the pipeline verifies taxonomy and locality with the GBIF API after mapping OCR output to Darwin Core. Any fields added by GBIF are recorded in the event log and written to the CSV output. Mismatches update the `flags` column so reviewers can spot corrections.

Toggle these checks and override API endpoints in the `[qc.gbif]` section of `config.toml`:

```toml
[qc.gbif]
enabled = true
species_match_endpoint = "https://api.gbif.org/v1/species/match"
reverse_geocode_endpoint = "https://api.gbif.org/v1/geocode/reverse"
```

See the [configuration](./configuration.md#gbif-endpoints) guide for details on these settings.
