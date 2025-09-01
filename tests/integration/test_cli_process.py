from __future__ import annotations

from pathlib import Path
from typing import Dict

from PIL import Image
from typer.testing import CliRunner

import cli


def _create_images(input_dir: Path, count: int = 2) -> None:
    input_dir.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        Image.new("RGB", (10, 10), color="white").save(input_dir / f"{i}.jpg")


def _patch_cli(monkeypatch, call_counter: Dict[str, int]) -> None:
    def fake_load_config(_: Path | None) -> Dict[str, object]:
        return {
            "ocr": {"preferred_engine": "stub", "enabled_engines": ["stub"]},
            "preprocess": {"pipeline": []},
            "gpt": {"model": "fake", "dry_run": True},
            "processing": {"retry_limit": 1},
            "qc": {},
            "pipeline": {"steps": ["image_to_text", "text_to_dwc"]},
        }

    def fake_available_engines(task: str) -> list[str]:
        return ["stub"]

    def fake_dispatch(task: str, **kwargs):
        call_counter["count"] += 1
        if task == "image_to_text":
            return "text", [1.0]
        if task == "text_to_dwc":
            return {
                "occurrenceID": kwargs.get("text", ""),
                "identificationHistory": [{"identificationID": "1"}],
            }, {}
        raise ValueError(task)

    monkeypatch.setattr(cli, "load_config", fake_load_config)
    monkeypatch.setattr(cli, "available_engines", fake_available_engines)
    monkeypatch.setattr(cli, "dispatch", fake_dispatch)


def _line_count(path: Path) -> int:
    return sum(1 for _ in path.open())


def test_process_generates_outputs(tmp_path: Path, monkeypatch) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    _create_images(input_dir)
    _patch_cli(monkeypatch, {"count": 0})

    runner = CliRunner()
    result = runner.invoke(
        cli.app, ["process", "--input", str(input_dir), "--output", str(output_dir)]
    )
    assert result.exit_code == 0

    assert (output_dir / "occurrence.csv").exists()
    assert (output_dir / "identification_history.csv").exists()
    assert (output_dir / "raw.jsonl").exists()
    assert (output_dir / "manifest.json").exists()

    # Two images plus header row
    assert _line_count(output_dir / "occurrence.csv") == 3
    assert _line_count(output_dir / "identification_history.csv") == 3
    assert _line_count(output_dir / "raw.jsonl") == 2


def test_resume_skips_processed_specimens(tmp_path: Path, monkeypatch) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    _create_images(input_dir)
    counter = {"count": 0}
    _patch_cli(monkeypatch, counter)

    runner = CliRunner()
    result = runner.invoke(
        cli.app, ["process", "--input", str(input_dir), "--output", str(output_dir)]
    )
    assert result.exit_code == 0
    initial_count = counter["count"]
    assert _line_count(output_dir / "occurrence.csv") == 3

    resume = runner.invoke(
        cli.app, ["resume", "--input", str(input_dir), "--output", str(output_dir)]
    )
    assert resume.exit_code == 0
    # No additional dispatch calls
    assert counter["count"] == initial_count
    # Outputs remain unchanged
    assert _line_count(output_dir / "occurrence.csv") == 3
    assert _line_count(output_dir / "raw.jsonl") == 2
