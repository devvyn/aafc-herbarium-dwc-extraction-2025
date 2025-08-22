from pathlib import Path
from typing import Iterable, Dict, Any
import csv
import json

# Use the canonical list of Darwin Core terms defined by the schema module
from dwc.schema import DWC_TERMS as DWC_COLUMNS

def write_manifest(output_dir: Path, meta: Dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(meta, indent=2))

def write_dwc_csv(output_dir: Path, rows: Iterable[Dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "dwc.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=DWC_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in DWC_COLUMNS})

def write_jsonl(output_dir: Path, events: Iterable[Dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / "raw.jsonl"
    with jsonl_path.open("w") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")
