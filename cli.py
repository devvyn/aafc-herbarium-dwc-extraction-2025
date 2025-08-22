from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import sys
from importlib import resources
from engines import dispatch

if sys.version_info >= (3, 11):
    import tomllib as tomli
else:  # pragma: no cover
    import tomli  # type: ignore

from io_utils.logs import setup_logging
from io_utils.read import iter_images, compute_sha256
from io_utils.write import write_dwc_csv, write_jsonl, write_manifest


def load_config(config_path: Optional[Path]) -> Dict[str, Any]:
    cfg_path = resources.files("config").joinpath("config.default.toml")
    with cfg_path.open("rb") as f:
        config = tomli.load(f)
    if config_path:
        with config_path.open("rb") as f:
            user_cfg = tomli.load(f)
        _deep_update(config, user_cfg)
    return config


def _deep_update(d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in u.items():
        if isinstance(v, dict) and isinstance(d.get(k), dict):
            _deep_update(d[k], v)
        else:
            d[k] = v
    return d


def process_cli(input_dir: Path, output: Path, config: Optional[Path] = None) -> None:
    """Core processing logic used by the command line interface.

    The current git commit hash is recorded in the output metadata when
    available. If the commit hash cannot be determined (e.g., not running
    inside a git repository), ``git_commit`` will be ``None``.
    """
    setup_logging(output)
    cfg = load_config(config)

    run_id = datetime.utcnow().isoformat()
    try:
        git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:  # pragma: no cover - git may not be available
        git_commit = None

    events = []
    dwc_rows = []
    for img_path in iter_images(input_dir):
        sha256 = compute_sha256(img_path)
        event = {
            "run_id": run_id,
            "image": img_path.name,
            "sha256": sha256,
            "engine": None,
            "engine_version": None,
            "dwc": {},
            "flags": [],
            "errors": [],
        }
        image_conf = 0.0
        if cfg.get("ocr", {}).get("allow_gpt") and image_conf < cfg.get("gpt", {}).get("fallback_threshold", 1.0):
            text, _ = dispatch(
                "image_to_text",
                image=img_path,
                model=cfg["gpt"]["model"],
                dry_run=cfg["gpt"]["dry_run"],
            )
            dwc_data, field_conf = dispatch(
                "text_to_dwc",
                text=text,
                model=cfg["gpt"]["model"],
                dry_run=cfg["gpt"]["dry_run"],
            )
            event["dwc"] = dwc_data
            event["dwc_confidence"] = field_conf
            event["engine"] = "gpt"
            event["engine_version"] = cfg["gpt"]["model"]

        events.append(event)
        dwc_rows.append(event["dwc"])

    meta = {
        "run_id": run_id,
        "started_at": run_id,
        "git_commit": git_commit,
        "config": cfg,
    }

    write_jsonl(output, events)
    write_dwc_csv(output, dwc_rows)
    write_manifest(output, meta)

    print(f"Processed {len(events)} images. Output written to {output}")


try:  # optional dependency
    import typer

    app = typer.Typer(help="Herbarium OCR to Darwin Core extractor")

    @app.command()
    def process(
        input: Path = typer.Option(
            ..., "--input", "-i", exists=True, file_okay=False, dir_okay=True, help="Directory of images"
        ),
        output: Path = typer.Option(
            ..., "--output", "-o", file_okay=False, dir_okay=True, help="Output directory"
        ),
        config: Optional[Path] = typer.Option(
            None,
            "--config",
            "-c",
            exists=True,
            dir_okay=False,
            file_okay=True,
            help="Optional config file",
        ),
    ) -> None:
        process_cli(input, output, config)

    if __name__ == "__main__":
        app()
except ModuleNotFoundError:  # pragma: no cover
    app = None
