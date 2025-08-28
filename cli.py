from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import sys
from importlib import resources
from engines import dispatch, available_engines, get_fallback_policy

if sys.version_info >= (3, 11):
    import tomllib as tomli
else:  # pragma: no cover
    import tomli  # type: ignore

from io_utils.logs import setup_logging
from io_utils.read import iter_images, compute_sha256
from io_utils.write import write_dwc_csv, write_jsonl, write_manifest
from preprocess import preprocess_image

import qc


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


def process_cli(
    input_dir: Path,
    output: Path,
    config: Optional[Path] = None,
    enabled_engines: Optional[List[str]] = None,
) -> None:
    """Core processing logic used by the command line interface.

    The current git commit hash is recorded in the output metadata when
    available. If the commit hash cannot be determined (e.g., not running
    inside a git repository), ``git_commit`` will be ``None``.
    """
    setup_logging(output)
    cfg = load_config(config)
    if enabled_engines is not None:
        cfg.setdefault("ocr", {})["enabled_engines"] = list(enabled_engines)
    qc.TOP_FIFTH_PCT = cfg.get("qc", {}).get("top_fifth_scan_pct", qc.TOP_FIFTH_PCT)

    run_id = datetime.utcnow().isoformat()
    try:
        git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:  # pragma: no cover - git may not be available
        git_commit = None

    events = []
    dwc_rows = []
    dupe_catalog: Dict[str, int] = {}
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
        pre_cfg = cfg.get("preprocess", {})
        pipeline = pre_cfg.get("pipeline", [])
        proc_path = preprocess_image(img_path, pre_cfg) if pipeline else img_path
        ocr_cfg = cfg.get("ocr", {})
        available = available_engines("image_to_text")
        enabled = ocr_cfg.get("enabled_engines")
        if enabled:
            available = [e for e in available if e in enabled]
        if not available:
            raise RuntimeError("No OCR engines available")
        preferred = ocr_cfg.get("preferred_engine", available[0])
        if preferred not in available:
            raise ValueError(
                f"Preferred engine '{preferred}' unavailable. Available: {', '.join(available)}"
            )
        if preferred == "tesseract" and sys.platform == "darwin" and not ocr_cfg.get(
            "allow_tesseract_on_macos", False
        ):
            preferred = "gpt" if "gpt" in available and ocr_cfg.get("allow_gpt") else available[0]
        if preferred == "gpt" and (not ocr_cfg.get("allow_gpt") or "gpt" not in available):
            preferred = available[0]

        text = ""
        confidences: list[float] = []
        try:
            text, confidences = dispatch("image_to_text", image=proc_path, engine=preferred)
            policy = get_fallback_policy(preferred)
            if policy:
                text, confidences, final_engine, engine_version = policy(
                    proc_path, text, confidences, cfg
                )
            else:
                final_engine, engine_version = preferred, None
            event["engine"] = final_engine
            if engine_version:
                event["engine_version"] = engine_version
        except Exception as exc:  # pragma: no cover - exercised in tests via monkeypatch
            event["errors"].append(str(exc))

        dwc_data, field_conf = dispatch(
            "text_to_dwc",
            text=text,
            model=cfg["gpt"]["model"],
            dry_run=cfg["gpt"]["dry_run"],
        )
        event["dwc"] = dwc_data
        event["dwc_confidence"] = field_conf

        qc_cfg = cfg.get("qc", {})
        flags = []
        flags.extend(qc.detect_duplicates(dupe_catalog, sha256, qc_cfg.get("phash_threshold", 0)))
        if qc_cfg.get("low_confidence_flag"):
            confidence = event.get("dwc_confidence")
            if isinstance(confidence, (int, float)):
                flags.extend(
                    qc.flag_low_confidence(
                        confidence, cfg.get("ocr", {}).get("confidence_threshold", 0.0)
                    )
                )
        scan_pct = event.get("scan_pct")
        if isinstance(scan_pct, (int, float)):
            flags.extend(qc.flag_top_fifth(scan_pct))
        if flags:
            event["flags"].extend(flags)

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
        enabled_engine: List[str] = typer.Option(
            None,
            "--engine",
            "-e",
            help="OCR engines to enable (repeatable)",
        ),
    ) -> None:
        process_cli(input, output, config, list(enabled_engine) if enabled_engine else None)

    if __name__ == "__main__":
        app()
except ModuleNotFoundError:  # pragma: no cover
    app = None
