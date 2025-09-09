# Export and reporting

## Darwin Core archive exports

Use the archive helpers to build Darwin Core files and bundle them with a manifest. The manifest records the export timestamp, commit hash and any filter criteria. When `compress=True`, provide a semantic version string so the bundle is saved as `dwca_v<version>.zip` under `output/`.

## Versioning guidelines

Tag every export with a semantic version. The accompanying `manifest.json` makes it possible to reproduce the dataset by recording filters and the exact code commit.
