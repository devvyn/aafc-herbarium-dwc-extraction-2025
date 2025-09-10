
.PHONY: setup manifest upload validate random-fetch

setup:
	uv sync

manifest:
	uv run python -m dataset_tool.scripts.build_manifest --src "$(SRC_DIR)" --out ./manifests/inventory-v1.jsonl

upload:
	uv run python -m dataset_tool.scripts.upload_dataset --src "$(SRC_DIR)" --manifest ./manifests/inventory-v1.jsonl

validate:
	uv run python -m dataset_tool.scripts.validate_manifest --manifest ./manifests/inventory-v1.jsonl

random-fetch:
	uv run python -m dataset_tool.scripts.random_fetch --manifest ./manifests/inventory-v1.jsonl --n $(N)
