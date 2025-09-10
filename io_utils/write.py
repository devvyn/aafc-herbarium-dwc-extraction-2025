from pathlib import Path
from typing import Iterable, Dict, Any
import csv
import json

# Use the canonical list of Darwin Core terms defined by the schema module
from dwc.schema import DWC_TERMS as DWC_COLUMNS

IDENT_HISTORY_COLUMNS = [
    "occurrenceID",
    "identificationID",
    "identifiedBy",
    "dateIdentified",
    "scientificName",
    "scientificNameAuthorship",
    "taxonRank",
    "identificationQualifier",
    "identificationRemarks",
    "identificationReferences",
    "identificationVerificationStatus",
    "isCurrent",
]


def write_manifest(output_dir: Path, meta: Dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(meta, indent=2))


def write_dwc_csv(output_dir: Path, rows: Iterable[Dict[str, Any]], append: bool = False) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "occurrence.csv"
    file_exists = csv_path.exists()
    mode = "a" if append and file_exists else "w"
    with csv_path.open(mode, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=DWC_COLUMNS)
        if not file_exists or mode == "w":
            writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in DWC_COLUMNS})


def write_identification_history_csv(
    output_dir: Path, rows: Iterable[Dict[str, Any]], append: bool = False
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "identification_history.csv"
    file_exists = csv_path.exists()
    mode = "a" if append and file_exists else "w"
    with csv_path.open(mode, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=IDENT_HISTORY_COLUMNS)
        if not file_exists or mode == "w":
            writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in IDENT_HISTORY_COLUMNS})


def write_jsonl(output_dir: Path, events: Iterable[Dict[str, Any]], append: bool = False) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / "raw.jsonl"
    mode = "a" if append and jsonl_path.exists() else "w"
    with jsonl_path.open(mode) as f:
        for event in events:
            f.write(json.dumps(event) + "\n")
