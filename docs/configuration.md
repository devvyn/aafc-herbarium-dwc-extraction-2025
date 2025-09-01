# Configuration overview

The toolkit reads settings from TOML files in the [`../config`](../config) directory. Run
`cli.py` with `--config` to overlay custom values on top of
[`config.default.toml`](../config/config.default.toml).

## Rules directory

Mapping and normalisation rules live under [`../config/rules`](../config/rules).

- [`dwc_rules.toml`](../config/rules/dwc_rules.toml) – placeholder for Darwin Core mapping rules.
- [`institutions.toml`](../config/rules/institutions.toml) – maps legacy institution codes to canonical values.
- [`vocab.toml`](../config/rules/vocab.toml) – reserved for future vocabulary normalisation.

These files support the mapping phase and are independent from preprocessing and OCR
artifacts stored in the pipeline database.

## GPT prompts and secrets

Prompt templates for the GPT engine reside in
[`../engines/gpt/prompts`](../engines/gpt/prompts). Adjust them to customise the
remote API requests. Configure the model and behaviour via the `[gpt]` section in
the configuration file. Set the `OPENAI_API_KEY` environment variable to supply
credentials securely—never hard-code API keys.

## Schema selection

The `[dwc]` section defaults to the Darwin Core plus ABCD data structure. Use the
`schema` and `schema_uri` keys to experiment with alternative schemas by providing
an appropriate namespace URI.
