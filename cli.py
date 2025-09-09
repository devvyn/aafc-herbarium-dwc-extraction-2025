from __future__ import annotations

import subprocess
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List
import sys
from importlib import resources
from sqlalchemy.orm import Session
from engines import dispatch, available_engines, get_fallback_policy

if sys.version_info >= (3, 11):
    import tomllib as tomli
else:  # pragma: no cover
    import tomli  # type: ignore

from io_utils.logs import setup_logging
from io_utils.read import iter_images, compute_sha256
from io_utils.write import (
    write_dwc_csv,
    write_jsonl,
    write_manifest,
    write_identification_history_csv,
)
from io_utils.candidates import (
    Candidate,
    init_db as init_candidate_db,
    insert_candidate,
)
from io_utils.database import (
    Specimen,
    ProcessingState,
    init_db as init_app_db,
    insert_specimen,
    fetch_processing_state,
    record_failure,
    upsert_processing_state,
)
from dwc import configure_terms, configure_mappings
from engines.errors import EngineError
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


def setup_run(
    output: Path, config: Optional[Path], enabled_engines: Optional[List[str]]
) -> Dict[str, Any]:
    """Prepare configuration and logging for a run."""
    setup_logging(output)
    cfg = load_config(config)
    dwc_cfg = cfg.get("dwc", {})
    schema_files = []
    for name in dwc_cfg.get("schema_files", []):
        path = Path(name)
        if not path.is_absolute():
            path = resources.files("config").joinpath("schemas", name)
        schema_files.append(path)
    if schema_files:
        configure_terms(schema_files)
    configure_mappings(dwc_cfg.get("custom", {}))
    if enabled_engines is not None:
        cfg.setdefault("ocr", {})["enabled_engines"] = list(enabled_engines)
    qc.TOP_FIFTH_PCT = cfg.get("qc", {}).get("top_fifth_scan_pct", qc.TOP_FIFTH_PCT)
    return cfg


def process_image(
    img_path: Path,
    cfg: Dict[str, Any],
    run_id: str,
    dupe_catalog: Dict[str, int],
    cand_session: Session,
    app_conn,
    retry_limit: int,
    resume: bool,
) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """Process a single image and return event data."""
    specimen_id = img_path.stem
    insert_specimen(app_conn, Specimen(specimen_id=specimen_id, image=img_path.name))
    state = fetch_processing_state(app_conn, specimen_id, "process")
    if resume and state and state.status == "done":
        return None, None, []
    if state and state.error and state.retries >= retry_limit:
        logging.warning("Skipping %s: retry limit reached", img_path.name)
        return None, None, []

    sha256 = compute_sha256(img_path)
    event: Dict[str, Any] = {
        "run_id": run_id,
        "image": img_path.name,
        "sha256": sha256,
        "engine": None,
        "engine_version": None,
        "dwc": {},
        "flags": [],
        "added_fields": [],
        "errors": [],
    }
    pre_cfg = cfg.get("preprocess", {})
    pipeline = pre_cfg.get("pipeline", [])
    proc_path = preprocess_image(img_path, pre_cfg) if pipeline else img_path
    pipeline_cfg = cfg.get("pipeline", {})
    steps = pipeline_cfg.get("steps", ["image_to_text", "text_to_dwc"])
    prompt_dir = resources.files("config").joinpath(cfg.get("gpt", {}).get("prompt_dir", "prompts"))
    ident_history_rows: List[Dict[str, Any]] = []
    try:
        text: str | None = None
        dwc_data: Dict[str, Any] = {}
        field_conf: Dict[str, Any] = {}
        for step in steps:
            section = "ocr" if step == "image_to_text" else step
            step_cfg = cfg.get(section, {})
            available = available_engines(step)
            enabled = step_cfg.get("enabled_engines")
            if enabled:
                available = [e for e in available if e in enabled]
            if not available:
                raise RuntimeError(f"No {step} engines available")
            preferred = step_cfg.get("preferred_engine", available[0])
            if preferred not in available:
                raise ValueError(
                    f"Preferred engine '{preferred}' unavailable for {step}. Available: {', '.join(available)}"
                )
            if (
                step == "image_to_text"
                and preferred == "tesseract"
                and sys.platform == "darwin"
                and not step_cfg.get("allow_tesseract_on_macos", False)
            ):
                preferred = (
                    "gpt" if "gpt" in available and step_cfg.get("allow_gpt") else available[0]
                )
            if (
                step == "image_to_text"
                and preferred == "gpt"
                and (not step_cfg.get("allow_gpt") or "gpt" not in available)
            ):
                preferred = available[0]

            if step == "image_to_text":
                kwargs: Dict[str, Any] = {}
                ocr_cfg = cfg.get("ocr", {})
                langs = ocr_cfg.get("langs")
                if langs and preferred != "paddleocr":
                    kwargs["langs"] = langs
                if preferred == "gpt":
                    gpt_cfg = cfg.get("gpt", {})
                    kwargs.update(
                        model=gpt_cfg.get("model", "gpt-4"),
                        dry_run=gpt_cfg.get("dry_run", False),
                        prompt_dir=prompt_dir,
                    )
                elif preferred == "tesseract":
                    t_cfg = cfg.get("tesseract", {})
                    kwargs.update(
                        oem=t_cfg.get("oem", 1),
                        psm=t_cfg.get("psm", 3),
                        extra_args=t_cfg.get("extra_args", []),
                    )
                    if t_cfg.get("model_paths"):
                        kwargs["model_paths"] = t_cfg["model_paths"]
                elif preferred == "paddleocr":
                    p_cfg = cfg.get("paddleocr", {})
                    kwargs.update(lang=p_cfg.get("lang", "en"))
                text, confidences = dispatch(
                    step, image=proc_path, engine=preferred, **kwargs
                )
                avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
                insert_candidate(
                    cand_session,
                    run_id,
                    img_path.name,
                    Candidate(value=text, engine=preferred, confidence=avg_conf),
                )
                policy = get_fallback_policy(preferred)
                if policy:
                    text, confidences, final_engine, engine_version = policy(
                        proc_path, text, confidences, cfg
                    )
                    if final_engine != preferred:
                        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
                        insert_candidate(
                    cand_session,
                            run_id,
                            img_path.name,
                            Candidate(value=text, engine=final_engine, confidence=avg_conf),
                        )
                else:
                    final_engine, engine_version = preferred, None
                event["engine"] = final_engine
                if engine_version:
                    event["engine_version"] = engine_version
            elif step == "text_to_dwc":
                gpt_cfg = cfg.get("gpt", {})
                dwc_data, field_conf = dispatch(
                    step,
                    text=text or "",
                    engine=preferred,
                    model=gpt_cfg.get("model", "gpt-4"),
                    dry_run=gpt_cfg.get("dry_run", False),
                    prompt_dir=prompt_dir,
                )
                ident_history = dwc_data.pop("identificationHistory", [])
                event["dwc"] = dwc_data
                event["dwc_confidence"] = field_conf
                if ident_history:
                    event["identification_history"] = ident_history
                    for ident in ident_history:
                        ident.setdefault("occurrenceID", dwc_data.get("occurrenceID", ""))
                        ident_history_rows.append(ident)
            elif step == "image_to_dwc":
                gpt_cfg = cfg.get("gpt", {})
                instructions = pipeline_cfg.get("image_to_dwc_instructions")
                if instructions is None:
                    raise ValueError(
                        "Missing pipeline.image_to_dwc_instructions for image_to_dwc step"
                    )
                dwc_data, field_conf = dispatch(
                    step,
                    image=proc_path,
                    instructions=instructions,
                    engine=preferred,
                    model=gpt_cfg.get("model", "gpt-4"),
                    dry_run=gpt_cfg.get("dry_run", False),
                )
                ident_history = dwc_data.pop("identificationHistory", [])
                event["dwc"] = dwc_data
                event["dwc_confidence"] = field_conf
                if ident_history:
                    event["identification_history"] = ident_history
                    for ident in ident_history:
                        ident.setdefault("occurrenceID", dwc_data.get("occurrenceID", ""))
                        ident_history_rows.append(ident)
            else:
                raise ValueError(f"Unsupported pipeline step: {step}")

        gbif_cfg = cfg.get("qc", {}).get("gbif", {})
        if gbif_cfg.get("enabled") and event.get("dwc"):
            gbif = qc.GbifLookup.from_config(cfg)
            original = event["dwc"].copy()
            try:
                updated = gbif.verify_taxonomy(event["dwc"])
                updated = gbif.verify_locality(updated)
            except Exception as exc:  # pragma: no cover - network issues
                event["errors"].append(str(exc))
            else:
                added = [k for k in updated if k not in original]
                changed = [k for k in original if updated.get(k) != original.get(k)]
                if added:
                    event["added_fields"].extend(added)
                if changed:
                    gbif_flags = [f"gbif:{f}" for f in changed]
                    event["flags"].extend(gbif_flags)
                    existing = updated.get("flags") or original.get("flags")
                    gbif_flag_str = ";".join(gbif_flags)
                    updated["flags"] = (
                        f"{existing};{gbif_flag_str}" if existing else gbif_flag_str
                    )
                event["dwc"] = updated

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

        avg_field_conf = sum(field_conf.values()) / len(field_conf) if field_conf else None
        upsert_processing_state(
            app_conn,
            ProcessingState(
                specimen_id=specimen_id,
                module="process",
                status="done",
                confidence=avg_field_conf,
            ),
        )
        return event, event["dwc"], ident_history_rows
    except ValueError:
        raise
    except EngineError as exc:
        event["errors"].append(str(exc))
        state = record_failure(app_conn, specimen_id, "process", exc.code, exc.message)
        if state.retries >= retry_limit:
            logging.warning("Skipping %s: retry limit reached", img_path.name)
        return event, None, []
    except Exception as exc:  # pragma: no cover - unexpected
        event["errors"].append(str(exc))
        state = record_failure(app_conn, specimen_id, "process", "UNKNOWN", str(exc))
        if state.retries >= retry_limit:
            logging.warning("Skipping %s: retry limit reached", img_path.name)
        return event, None, []


def write_outputs(
    output: Path,
    events: List[Dict[str, Any]],
    dwc_rows: List[Dict[str, Any]],
    ident_history_rows: List[Dict[str, Any]],
    meta: Dict[str, Any],
    append: bool,
) -> None:
    """Write all output artifacts for a run."""
    if events:
        write_jsonl(output, events, append=append)
    if dwc_rows:
        write_dwc_csv(output, dwc_rows, append=append)
    if ident_history_rows:
        write_identification_history_csv(output, ident_history_rows, append=append)
    write_manifest(output, meta)


def process_cli(
    input_dir: Path,
    output: Path,
    config: Optional[Path] = None,
    enabled_engines: Optional[List[str]] = None,
    resume: bool = False,
) -> None:
    """Core processing logic used by the command line interface.

    The current git commit hash is recorded in the output metadata when
    available. If the commit hash cannot be determined (e.g., not running
    inside a git repository), ``git_commit`` will be ``None``.
    """
    cfg = setup_run(output, config, enabled_engines)

    run_id = datetime.now(timezone.utc).isoformat()
    try:
        git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:  # pragma: no cover - git may not be available
        git_commit = None

    events: List[Dict[str, Any]] = []
    dwc_rows: List[Dict[str, Any]] = []
    ident_history_rows: List[Dict[str, Any]] = []
    dupe_catalog: Dict[str, int] = {}
    cand_session = init_candidate_db(output / "candidates.db")
    app_conn = init_app_db(output / "app.db")
    retry_limit = cfg.get("processing", {}).get("retry_limit", 3)
    for img_path in iter_images(input_dir):
        event, dwc_row, ident_rows = process_image(
            img_path,
            cfg,
            run_id,
            dupe_catalog,
            cand_session,
            app_conn,
            retry_limit,
            resume,
        )
        if event is None:
            continue
        events.append(event)
        if dwc_row:
            dwc_rows.append(dwc_row)
        ident_history_rows.extend(ident_rows)

    meta = {
        "run_id": run_id,
        "started_at": run_id,
        "git_commit": git_commit,
        "config": cfg,
    }

    write_outputs(output, events, dwc_rows, ident_history_rows, meta, resume)
    cand_session.close()
    app_conn.close()

    logging.info("Processed %d images. Output written to %s", len(events), output)


try:  # optional dependency
    import typer

    app = typer.Typer(help="Herbarium OCR to Darwin Core extractor")

    @app.command()
    def process(
        input: Path = typer.Option(
            ...,
            "--input",
            "-i",
            exists=True,
            file_okay=False,
            dir_okay=True,
            help="Directory of images",
        ),
        output: Path = typer.Option(
            ...,
            "--output",
            "-o",
            file_okay=False,
            dir_okay=True,
            help="Output directory",
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
        process_cli(
            input,
            output,
            config,
            list(enabled_engine) if enabled_engine else None,
            resume=False,
        )

    @app.command()
    def resume(
        input: Path = typer.Option(
            ...,
            "--input",
            "-i",
            exists=True,
            file_okay=False,
            dir_okay=True,
            help="Directory of images",
        ),
        output: Path = typer.Option(
            ...,
            "--output",
            "-o",
            file_okay=False,
            dir_okay=True,
            help="Output directory",
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
        process_cli(
            input,
            output,
            config,
            list(enabled_engine) if enabled_engine else None,
            resume=True,
        )

    if __name__ == "__main__":
        app()
except ModuleNotFoundError:  # pragma: no cover
    app = None
