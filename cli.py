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
from engines.language_codes import normalize_iso2, normalize_iso3, to_iso2

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
from io_utils.ocr_cache import (
    init_db as init_ocr_cache_db,
    get_cached_ocr,
    cache_ocr_result,
    record_run,
    complete_run,
    record_lineage,
    get_cache_stats,
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
from dwc.archive import create_archive
from engines.errors import EngineError
from preprocess import preprocess_image

import qc


def _prepare_ocr_languages(
    preferred: str, raw_langs: Optional[List[str]]
) -> tuple[Optional[List[str]], Optional[str]]:
    """Return normalized language hints for an OCR engine.

    Parameters
    ----------
    preferred:
        Name of the engine currently selected for ``image_to_text``.
    raw_langs:
        Values from ``[ocr].langs`` in the configuration.  The list may contain
        ISO 639-1 or 639-2 codes in any mix of upper or lower case.

    Returns
    -------
    tuple
        ``(langs, primary)`` where ``langs`` is the list passed to the engine's
        ``langs`` parameter and ``primary`` is the best single-language hint for
        engines such as PaddleOCR that expect a dedicated ``lang`` argument.
    """

    if not raw_langs:
        return None, None

    try:
        if preferred == "tesseract":
            normalized = normalize_iso3(raw_langs)
            return normalized, None
        if preferred in {"paddleocr", "multilingual"}:
            normalized = normalize_iso2(raw_langs)
            primary = normalized[0] if normalized else None
            return normalized, primary
        return raw_langs, None
    except ValueError as exc:
        raise ValueError(f"Invalid [ocr].langs entry for {preferred}: {exc}") from exc


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
    cache_session: Session,
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
        ocr_cfg = cfg.get("ocr", {})
        raw_langs = ocr_cfg.get("langs")
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
                # Check cache first
                specimen_sha = compute_sha256(img_path)
                cached = get_cached_ocr(cache_session, specimen_sha, preferred)

                if cached and not cached.error:
                    # Use cached result
                    text = cached.extracted_text
                    confidences = [cached.confidence]
                    avg_conf = cached.confidence
                    record_lineage(cache_session, run_id, specimen_sha, "cached", cache_hit=True)
                else:
                    # Run OCR
                    kwargs: Dict[str, Any] = {}
                    lang_hints, primary_lang = _prepare_ocr_languages(preferred, raw_langs)
                    if lang_hints:
                        kwargs["langs"] = lang_hints
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
                        if lang_hints:
                            kwargs["langs"] = lang_hints
                        if t_cfg.get("model_paths"):
                            kwargs["model_paths"] = t_cfg["model_paths"]
                    elif preferred == "paddleocr":
                        p_cfg = cfg.get("paddleocr", {})
                        language = p_cfg.get("lang")
                        if language:
                            try:
                                language = to_iso2(language)
                            except ValueError as exc:
                                raise ValueError(f"Invalid [paddleocr].lang value: {exc}") from exc
                        elif primary_lang:
                            language = primary_lang
                        kwargs["lang"] = language or "en"
                    text, confidences = dispatch(step, image=proc_path, engine=preferred, **kwargs)
                    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

                    # Cache the result
                    cache_ocr_result(
                        cache_session,
                        specimen_sha,
                        preferred,
                        text,
                        avg_conf,
                    )
                    record_lineage(cache_session, run_id, specimen_sha, "completed", cache_hit=False)
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
                dwc_cfg = cfg.get("dwc", {})
                # Use rule-based extraction by default (free tier)
                # Override: Set dwc.preferred_engine="gpt" to use GPT extraction
                dwc_engine = dwc_cfg.get("preferred_engine", "rules")
                dwc_data, field_conf = dispatch(
                    step,
                    text=text or "",
                    engine=dwc_engine,
                    model=gpt_cfg.get("model", "gpt-4"),
                    dry_run=gpt_cfg.get("dry_run", False),
                    prompt_dir=prompt_dir,
                    fields=dwc_cfg.get("strict_minimal_fields"),
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
            verification_metadata = {}

            try:
                # Enhanced taxonomy verification with metadata
                updated, taxonomy_meta = gbif.verify_taxonomy(event["dwc"])
                verification_metadata["taxonomy"] = taxonomy_meta

                # Enhanced locality verification with metadata
                updated, locality_meta = gbif.verify_locality(updated)
                verification_metadata["locality"] = locality_meta

                # Optional occurrence validation
                if gbif_cfg.get("enable_occurrence_validation", False):
                    updated, occurrence_meta = gbif.validate_occurrence(updated)
                    verification_metadata["occurrence"] = occurrence_meta

            except Exception as exc:  # pragma: no cover - network issues
                event["errors"].append(f"GBIF verification error: {str(exc)}")
            else:
                # Track field additions and changes
                added = [k for k in updated if k not in original]
                changed = [k for k in original if updated.get(k) != original.get(k)]

                # Collect verification issues for flagging
                gbif_issues = []
                for verify_type, meta in verification_metadata.items():
                    if isinstance(meta, dict) and "gbif_issues" in meta:
                        for issue in meta["gbif_issues"]:
                            gbif_issues.append(f"{verify_type}:{issue}")

                # Add verification metadata to event
                event["gbif_verification"] = verification_metadata

                if added:
                    event["added_fields"].extend(added)

                # Create flags for changes and issues
                all_flags = []
                if changed:
                    gbif_flags = [f"gbif_updated:{f}" for f in changed]
                    all_flags.extend(gbif_flags)

                if gbif_issues:
                    issue_flags = [f"gbif_issue:{issue}" for issue in gbif_issues]
                    all_flags.extend(issue_flags)

                if all_flags:
                    event["flags"].extend(all_flags)
                    existing = updated.get("flags") or original.get("flags")
                    gbif_flag_str = ";".join(all_flags)
                    updated["flags"] = f"{existing};{gbif_flag_str}" if existing else gbif_flag_str

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
    # Import progress tracker
    try:
        from progress_tracker import global_tracker, track_processing
        use_progress = True
    except ImportError:
        use_progress = False

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
    cache_session = init_ocr_cache_db(output / "ocr_cache.db")
    retry_limit = cfg.get("processing", {}).get("retry_limit", 3)

    # Record this processing run
    record_run(cache_session, run_id, cfg)

    # Count total images for progress tracking
    image_list = list(iter_images(input_dir))
    total_images = len(image_list)

    # Start progress tracking
    if use_progress:
        global_tracker.start_processing(total_images, {"engine": enabled_engines})

    for img_path in image_list:
        # Update progress tracker
        if use_progress:
            global_tracker.image_started(img_path)

        event, dwc_row, ident_rows = process_image(
            img_path,
            cfg,
            run_id,
            dupe_catalog,
            cand_session,
            cache_session,
            app_conn,
            retry_limit,
            resume,
        )

        # Update progress based on result
        if use_progress:
            if event is None:
                global_tracker.image_skipped(img_path, "Resume mode - already processed")
            elif event.get("errors"):
                error_msg = event["errors"][0] if event["errors"] else "Unknown error"
                global_tracker.image_failed(img_path, error_msg)
            else:
                engine = event.get("engine", "unknown")
                confidence = event.get("dwc_confidence")
                if isinstance(confidence, dict) and confidence:
                    avg_conf = sum(confidence.values()) / len(confidence)
                else:
                    avg_conf = confidence if isinstance(confidence, (int, float)) else None
                global_tracker.image_completed(img_path, engine, avg_conf)

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

    # Complete progress tracking
    if use_progress:
        global_tracker.processing_complete()

    # Mark run as complete and log cache stats
    complete_run(cache_session, run_id)
    cache_stats = get_cache_stats(cache_session, run_id)
    logging.info(
        "Processed %d images. Output written to %s | Cache stats: %d hits, %d new OCR, %.1f%% hit rate",
        len(events),
        output,
        cache_stats["cache_hits"],
        cache_stats["new_ocr"],
        cache_stats["cache_hit_rate"] * 100,
    )


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

    @app.command()
    def export(
        output: Path = typer.Option(
            ...,
            "--output",
            "-o",
            exists=True,
            file_okay=False,
            dir_okay=True,
            help="Directory containing DwC CSV files to export",
        ),
        version: str = typer.Option(
            "1.0.0",
            "--version",
            "-v",
            help="Semantic version for the export bundle",
        ),
        bundle_format: str = typer.Option(
            "rich",
            "--format",
            "-f",
            help="Bundle format: 'rich' (with metadata) or 'simple' (version only)",
        ),
        include_checksums: bool = typer.Option(
            True,
            "--checksums/--no-checksums",
            help="Include file checksums in manifest",
        ),
        compress: bool = typer.Option(
            True,
            "--compress/--no-compress",
            help="Create compressed ZIP archive",
        ),
        config: Optional[Path] = typer.Option(
            None,
            "--config",
            "-c",
            exists=True,
            dir_okay=False,
            file_okay=True,
            help="Optional config file for export settings",
        ),
    ) -> None:
        """Create a versioned Darwin Core Archive export bundle."""
        import re

        # Validate semantic version
        semver_pattern = re.compile(r"^\d+\.\d+\.\d+$")
        if not semver_pattern.match(version):
            typer.echo(f"Error: Version '{version}' must follow semantic versioning (e.g., '1.0.0')", err=True)
            raise typer.Exit(1)

        # Validate bundle format
        if bundle_format not in ["rich", "simple"]:
            typer.echo(f"Error: Bundle format must be 'rich' or 'simple', got '{bundle_format}'", err=True)
            raise typer.Exit(1)

        # Load configuration for export settings
        cfg = load_config(config)
        export_cfg = cfg.get("export", {})

        # Override config with CLI options
        filters = None  # Could be extended to accept filter criteria
        additional_files = export_cfg.get("additional_files", [])

        try:
            archive_path = create_archive(
                output,
                compress=compress,
                version=version,
                filters=filters,
                bundle_format=bundle_format,
                include_checksums=include_checksums,
                additional_files=additional_files,
            )

            if compress:
                typer.echo(f"✅ Export bundle created: {archive_path}")
                typer.echo(f"📊 Format: {bundle_format}")
                typer.echo(f"🏷️  Version: {version}")
                if include_checksums:
                    typer.echo("🔐 Checksums: included")
            else:
                typer.echo(f"✅ DwC-A files prepared in: {output}")
                typer.echo(f"📄 Meta.xml created: {archive_path}")

        except Exception as e:
            typer.echo(f"❌ Export failed: {e}", err=True)
            raise typer.Exit(1)

    if __name__ == "__main__":
        app()
except ModuleNotFoundError:  # pragma: no cover
    app = None
