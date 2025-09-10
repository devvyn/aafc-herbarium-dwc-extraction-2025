from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import subprocess
from typing import List, Dict, Any

import pyexcel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .candidate_models import Candidate as CandidateModel


def build_manifest(schema_version: str) -> Dict[str, str]:
    """Create version metadata with commit hash and timestamp."""
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    timestamp = datetime.now(timezone.utc).isoformat()
    return {"commit": commit, "timestamp": timestamp, "schema_version": schema_version}


def export_candidates_to_spreadsheet(
    session: Session,
    schema_version: str,
    output_path: Path,
    gsheet_title: str | None = None,
    creds_path: Path | None = None,
) -> Path:
    """
    Export all candidate records to an Excel spreadsheet with manifest metadata.

    If ``gsheet_title`` and ``creds_path`` are provided, also upload to Google Sheets.
    """
    rows = session.execute(
        select(
            CandidateModel.run_id,
            CandidateModel.image,
            CandidateModel.value,
            CandidateModel.engine,
            CandidateModel.confidence,
            CandidateModel.error,
        )
    ).all()
    header = ["run_id", "image", "value", "engine", "confidence", "error", "selected"]
    sheet = [header]
    for row in rows:
        sheet.append(list(row) + [""])
    manifest = build_manifest(schema_version)
    manifest_sheet = [["key", "value"]] + [[k, v] for k, v in manifest.items()]
    pyexcel.save_book_as(
        bookdict={"candidates": sheet, "manifest": manifest_sheet},
        dest_file_name=str(output_path),
    )

    if gsheet_title and creds_path:
        import pygsheets

        gc = pygsheets.authorize(service_file=str(creds_path))
        sh = gc.create(gsheet_title)
        sh.sheet1.update_values("A1", sheet)
        manifest_ws = sh.add_worksheet("manifest")
        manifest_ws.update_values("A1", manifest_sheet)
    return output_path


def import_review_selections(spreadsheet: Path, schema_version: str) -> List[Dict[str, Any]]:
    """Read reviewer selections and validate manifest data."""
    book = pyexcel.get_book(file_name=str(spreadsheet))
    manifest_sheet = book["manifest"]
    manifest_rows = list(manifest_sheet.array)
    manifest = {row[0]: row[1] for row in manifest_rows[1:]}

    expected = build_manifest(schema_version)
    for key in ("commit", "schema_version"):
        if manifest.get(key) != expected[key]:
            raise ValueError(f"manifest mismatch for {key}")

    cand_sheet = book["candidates"]
    cand_sheet.name_columns_by_row(0)
    decisions: List[Dict[str, Any]] = []
    for record in cand_sheet.to_records():
        selected = str(record.get("selected", "")).strip().lower()
        if selected in {"1", "true", "yes", "y"}:
            decisions.append(
                {
                    "run_id": record.get("run_id"),
                    "image": record.get("image"),
                    "value": record.get("value"),
                    "engine": record.get("engine"),
                }
            )
    return decisions


__all__ = ["export_candidates_to_spreadsheet", "import_review_selections", "build_manifest"]
