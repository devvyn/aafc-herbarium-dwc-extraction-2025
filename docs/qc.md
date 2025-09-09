# Quality control review

During the QC phase, confirm OCR candidates alongside the source image.

```bash
python review.py --tui path/to/candidates.db specimen.jpg
```

Use the arrow keys to highlight a candidate and press Enter to confirm. The chosen value is persisted through [`io_utils.candidates.record_decision`](../io_utils/candidates.py). If the terminal cannot display images, a text placeholder is shown instead.

## Override GBIF endpoints

The default [GBIF](https://www.gbif.org/) URLs used for taxonomy and locality
checks can be replaced via the configuration file. Add a `[gbif]` section to
your config and supply alternative endpoints:

```toml
[gbif]
species_match_endpoint = "https://example.org/species"
reverse_geocode_endpoint = "https://example.org/geocode"
```

These values override the defaults from `config.default.toml` and are applied
when running any QC-related commands.
