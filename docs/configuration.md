# Configuration overview

The toolkit reads settings from TOML files in the [`../config`](../config) directory. Run
`cli.py` with `--config` to overlay custom values on top of
[`config.default.toml`](../config/config.default.toml).

## Pipeline steps

The `[pipeline]` section lists high-level tasks to run for each image.
Steps run in order and use the preferred engine from their matching
configuration section. The default pipeline processes text and maps it
to Darwin Core terms:

```toml
[pipeline]
steps = ["image_to_text", "text_to_dwc"]
```

## Preprocessing settings

Image cleanup steps live in the `[preprocess]` section. Use `pipeline` to list
preprocessors and `binarize_method` to switch between global Otsu and adaptive
Sauvola thresholding:

```toml
[preprocess]
pipeline = ["grayscale", "deskew", "binarize", "resize"]
binarize_method = "adaptive"  # or "otsu"
max_dim_px = 4000
contrast_factor = 1.5  # used when "contrast" is in the pipeline
```

## Rules directory

Mapping and normalisation rules live under [`../config/rules`](../config/rules).

- [`dwc_rules.toml`](../config/rules/dwc_rules.toml) – transformation rules for raw OCR fields
  such as `collector` → `recordedBy` and `collection date` → `eventDate`.
- [`institutions.toml`](../config/rules/institutions.toml) – maps legacy institution codes to canonical values.
- [`vocab.toml`](../config/rules/vocab.toml) – vocabulary normalisation tables including
  `basisOfRecord` and `sex` mappings based on GBIF vocabularies.

These files support the mapping phase and are independent from preprocessing and OCR
artifacts stored in the pipeline database.

## GPT prompts and secrets

Prompt templates for the GPT engine reside in
[`../config/prompts`](../config/prompts). Adjust them or change
`gpt.prompt_dir` to customise the remote API requests. Configure the model and
behaviour via the `[gpt]` section in the configuration file. Set the
`OPENAI_API_KEY` environment variable (for example via `.env`) to supply
credentials securely—never hard-code API keys.

## Schema selection

The `[dwc]` section defaults to the Darwin Core plus ABCD data structure. Use
`schema_files` to reference alternative XSDs or adjust the `schema_uri` to
experiment with other vocabularies.

## GBIF endpoints

Quality-control tasks can query GBIF for taxonomy and locality validation. Override the default API endpoints by setting the `[qc.gbif]` section:

```toml
[qc.gbif]
species_match_endpoint = "https://api.gbif.org/v1/species/match"
reverse_geocode_endpoint = "https://api.gbif.org/v1/geocode/reverse"
```
