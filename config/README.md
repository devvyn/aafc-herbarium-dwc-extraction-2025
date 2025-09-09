# Configuration files

This package bundles default configuration and auxiliary resources used by the
application.

- `config.default.toml` – base settings merged with any user-provided
  configuration.
- `prompts/` – ChatGPT prompt templates loaded by the GPT engine.
- `schemas/` – Darwin Core and ABCD schema definitions used to populate field
  lists.
- `rules/` – mapping and normalisation tables applied during data cleaning.
  See [mapping and vocabulary](../docs/mapping_and_vocabulary.md) for details.

## Custom term mappings

Override built-in field aliases by adding a `[dwc.custom]` section to your
configuration. Each key maps a raw field name to a Darwin Core term:

```toml
[dwc.custom]
barcode = "catalogNumber"
```
