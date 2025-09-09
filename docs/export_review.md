# Export review

## Versioning scheme

DwC-A exports are written under `./output/` using a version tag. When `compress=True` the archive is named `dwca-<version>.zip`; otherwise sidecar files are written directly to the directory. By default `<version>` is the current UTC timestamp, but a semantic version string may be supplied.

Each export also includes a `manifest.json` containing the timestamp, commit hash, and any filters applied during export so that results can be reproduced.
