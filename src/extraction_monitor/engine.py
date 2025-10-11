"""
Extraction Monitoring Engine

Unified data reader for both TUI and web dashboards.
Reads raw.jsonl, environment.json to provide real-time extraction stats.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ExtractionStats:
    """Extraction statistics."""

    run_id: str
    model_name: str
    total_specimens: int
    completed: int
    failed: int
    success_rate: float
    field_stats: Dict[str, float]  # field -> extraction rate %
    latest_events: List[dict]
    elapsed_seconds: Optional[float] = None
    throughput: Optional[float] = None  # specimens/minute


class ExtractionMonitorEngine:
    """Engine for monitoring extraction runs."""

    @staticmethod
    def find_latest_run(base_dir: Path = Path("full_dataset_processing")) -> Optional[Path]:
        """Find the most recent extraction run directory."""
        if not base_dir.exists():
            return None

        runs = [d for d in base_dir.iterdir() if d.is_dir() and (d / "raw.jsonl").exists()]
        if not runs:
            return None

        # Sort by modification time
        latest = max(runs, key=lambda d: (d / "raw.jsonl").stat().st_mtime)
        return latest

    @staticmethod
    def get_all_runs(base_dir: Path = Path("full_dataset_processing")) -> List[Path]:
        """Get all extraction run directories."""
        if not base_dir.exists():
            return []

        runs = [d for d in base_dir.iterdir() if d.is_dir() and (d / "raw.jsonl").exists()]
        # Sort by modification time, newest first
        return sorted(runs, key=lambda d: (d / "raw.jsonl").stat().st_mtime, reverse=True)

    @staticmethod
    def read_extraction_stats(run_dir: Path) -> ExtractionStats:
        """
        Read extraction statistics from run directory.

        Args:
            run_dir: Path to extraction run directory

        Returns:
            ExtractionStats object
        """
        run_id = run_dir.name
        model_name = "Unknown Model"
        total_specimens = 0
        elapsed_seconds = None

        # Read environment.json for metadata
        env_file = run_dir / "environment.json"
        if env_file.exists():
            with open(env_file) as f:
                env_data = json.load(f)
                model_name = env_data.get("model", "Unknown Model")

                # Extract total from command or assume full dataset
                command = env_data.get("command", "")
                if "--limit" in command:
                    import re

                    match = re.search(r"--limit\s+(\d+)", command)
                    if match:
                        total_specimens = int(match.group(1))
                else:
                    # No limit = full dataset
                    total_specimens = 2885

                # Calculate elapsed time if we have timestamp
                if "timestamp" in env_data:
                    start_time = datetime.fromisoformat(env_data["timestamp"])
                    elapsed_seconds = (datetime.now(start_time.tzinfo) - start_time).total_seconds()

        # Read raw.jsonl for extraction results
        raw_file = run_dir / "raw.jsonl"
        results = []
        if raw_file.exists():
            with open(raw_file) as f:
                for line in f:
                    if line.strip():
                        try:
                            results.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue  # Skip malformed lines

        completed = len(results)
        failed = sum(1 for r in results if "error" in r or not r.get("dwc"))
        successful = completed - failed
        success_rate = (successful / completed * 100) if completed > 0 else 0

        # Calculate field extraction rates
        field_counts = {}
        successful_results = [r for r in results if "dwc" in r and r["dwc"]]

        for result in successful_results:
            for field in result["dwc"].keys():
                field_counts[field] = field_counts.get(field, 0) + 1

        field_stats = {}
        if successful_results:
            field_stats = {
                field: (count / len(successful_results)) * 100
                for field, count in field_counts.items()
            }

        # Calculate throughput
        throughput = None
        if elapsed_seconds and elapsed_seconds > 0:
            throughput = (completed / elapsed_seconds) * 60  # specimens/minute

        # Get latest events
        latest_events = results[-20:]  # Last 20 events

        return ExtractionStats(
            run_id=run_id,
            model_name=model_name,
            total_specimens=total_specimens,
            completed=completed,
            failed=failed,
            success_rate=success_rate,
            field_stats=field_stats,
            latest_events=latest_events,
            elapsed_seconds=elapsed_seconds,
            throughput=throughput,
        )
