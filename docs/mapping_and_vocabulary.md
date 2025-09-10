# Mapping and vocabulary

During the mapping phase, OCR output is normalised before loading into the
primary DwC+ABCD database. Field aliases are resolved using
[dwc_rules.toml](../config/rules/dwc_rules.toml), while controlled vocabulary
values such as `basisOfRecord` and `typeStatus` are defined in
[vocab.toml](../config/rules/vocab.toml).

See the [configuration README](../config/README.md) for an overview of all
available rule files.

## Field mapping example

Create a custom alias for `barcode` by adding a `[dwc.custom]` section to the
configuration:

```toml
[dwc.custom]
barcode = "catalogNumber"
```

With this configuration, the mapping function converts OCR output:

```python
from dwc import configure_mappings, map_ocr_to_dwc

configure_mappings({"barcode": "catalogNumber"})
record = map_ocr_to_dwc({"barcode": "ABC123"})
```

The resulting `record.catalogNumber` is `"ABC123"`.

The default rules already map common labels such as `collector number` to
`recordNumber` via [`dwc_rules.toml`](../config/rules/dwc_rules.toml).

## Future work

Custom schema mapping via the `[dwc]` configuration section will allow external field definitions to be translated without modifying core code (Issue TBD). Additional mapping rules will be populated in `config/rules/dwc_rules.toml` and `config/rules/vocab.toml` (Issue TBD).

## Vocabulary normalisation example

Controlled terms such as `basisOfRecord` are harmonised via
[`vocab.toml`](../config/rules/vocab.toml):

```python
from dwc import normalize_vocab

normalize_vocab("herbarium sheet", "basisOfRecord")
```

This call returns `"PreservedSpecimen"`.

Passing `"field note"` instead normalises the value to `"HumanObservation"`.
