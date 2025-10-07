"""
Batch Monitoring Engine

Core functionality for tracking OpenAI Batch API jobs.
Consumed by terminal and web UIs.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from .models import BatchStatus, ProgressMetrics, TimeMetrics


class BatchMonitorEngine:
    """Core engine for batch monitoring."""

    def __init__(self, history_file: Optional[Path] = None):
        """
        Initialize monitoring engine.

        Args:
            history_file: Optional path to store batch history
        """
        if OpenAI is None:
            raise ImportError("OpenAI SDK not installed. Run: uv add openai")

        self.client = OpenAI()
        self.history_file = history_file or Path("batch_history.jsonl")

    def fetch_status(self, batch_id: str) -> BatchStatus:
        """
        Fetch current status of a batch job from OpenAI.

        Args:
            batch_id: OpenAI batch ID

        Returns:
            BatchStatus with current state
        """
        # Fetch from OpenAI API
        batch = self.client.batches.retrieve(batch_id)

        # Parse progress
        request_counts = batch.request_counts
        progress = ProgressMetrics(
            total=request_counts.total if request_counts else 0,
            completed=request_counts.completed if request_counts else 0,
            failed=request_counts.failed if request_counts else 0,
        )

        # Parse timing
        timing = TimeMetrics(
            created_at=datetime.fromtimestamp(batch.created_at),
            started_at=(
                datetime.fromtimestamp(batch.in_progress_at)
                if batch.in_progress_at
                else None
            ),
            completed_at=(
                datetime.fromtimestamp(batch.completed_at) if batch.completed_at else None
            ),
            expires_at=datetime.fromtimestamp(batch.expires_at),
        )

        # Build status
        status = BatchStatus(
            batch_id=batch_id,
            status=batch.status,
            progress=progress,
            timing=timing,
            output_file_id=batch.output_file_id,
            error_file_id=batch.error_file_id,
            errors=batch.errors,
        )

        # Store in history
        if self.history_file:
            self._append_history(status)

        return status

    def fetch_multiple(self, batch_ids: List[str]) -> List[BatchStatus]:
        """
        Fetch status for multiple batch jobs.

        Args:
            batch_ids: List of batch IDs

        Returns:
            List of BatchStatus objects
        """
        return [self.fetch_status(batch_id) for batch_id in batch_ids]

    def get_active_batches(self) -> List[str]:
        """
        Get list of batch IDs currently being tracked.

        Scans full_dataset_processing directory for batch_id.txt files.

        Returns:
            List of batch IDs
        """
        batch_ids = []
        base_dir = Path("full_dataset_processing")

        if not base_dir.exists():
            return batch_ids

        # Find all batch_id.txt files
        for batch_file in base_dir.rglob("batch_id.txt"):
            try:
                batch_id = batch_file.read_text().strip()
                if batch_id:
                    batch_ids.append(batch_id)
            except Exception:
                continue

        return batch_ids

    def load_history(self, batch_id: Optional[str] = None) -> List[dict]:
        """
        Load batch history from file.

        Args:
            batch_id: Optional filter for specific batch

        Returns:
            List of history entries
        """
        if not self.history_file.exists():
            return []

        history = []
        with open(self.history_file, "r") as f:
            for line in f:
                entry = json.loads(line)
                if batch_id is None or entry.get("batch_id") == batch_id:
                    history.append(entry)

        return history

    def _append_history(self, status: BatchStatus):
        """Append status to history file."""
        entry = {
            "batch_id": status.batch_id,
            "status": status.status,
            "progress": {
                "total": status.progress.total,
                "completed": status.progress.completed,
                "failed": status.progress.failed,
            },
            "timestamp": datetime.now().isoformat(),
            "elapsed_minutes": status.timing.elapsed_minutes,
            "completion_percentage": status.progress.completion_percentage,
        }

        with open(self.history_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
