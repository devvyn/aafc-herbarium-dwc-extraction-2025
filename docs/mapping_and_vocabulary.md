# Mapping and vocabulary

During the mapping phase, OCR output is normalised before loading into the
primary DwC+ABCD database. Field aliases are resolved using
[dwc_rules.toml](../config/rules/dwc_rules.toml), while controlled vocabulary
values such as `basisOfRecord` and `typeStatus` are defined in
[vocab.toml](../config/rules/vocab.toml).

See the [configuration README](../config/README.md) for an overview of all
available rule files.
