"""
Data models for batch monitoring system.

Shared by terminal and web UIs.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ProgressMetrics:
    """Progress statistics for a batch job."""

    total: int
    completed: int
    failed: int

    @property
    def completion_rate(self) -> float:
        """Percentage of requests completed (0.0-1.0)."""
        if self.total == 0:
            return 0.0
        return self.completed / self.total

    @property
    def completion_percentage(self) -> float:
        """Percentage of requests completed (0-100)."""
        return self.completion_rate * 100

    @property
    def failure_rate(self) -> float:
        """Percentage of requests failed (0.0-1.0)."""
        if self.total == 0:
            return 0.0
        return self.failed / self.total


@dataclass
class TimeMetrics:
    """Timing information for a batch job."""

    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    expires_at: datetime

    @property
    def elapsed_seconds(self) -> float:
        """Seconds elapsed since batch started."""
        if not self.started_at:
            return 0.0

        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()

    @property
    def remaining_seconds(self) -> float:
        """Seconds until batch expires."""
        return (self.expires_at - datetime.now()).total_seconds()

    @property
    def elapsed_minutes(self) -> float:
        """Minutes elapsed since batch started."""
        return self.elapsed_seconds / 60

    @property
    def remaining_hours(self) -> float:
        """Hours until batch expires."""
        return self.remaining_seconds / 3600

    def estimate_completion_seconds(self, progress: ProgressMetrics) -> Optional[float]:
        """Estimate seconds until completion based on current progress."""
        if progress.completion_rate == 0:
            return None
        if progress.completion_rate >= 1.0:
            return 0.0

        # Estimate: elapsed_time / completion_rate = total_time
        # remaining = total_time - elapsed_time
        estimated_total = self.elapsed_seconds / progress.completion_rate
        return estimated_total - self.elapsed_seconds


@dataclass
class BatchStatus:
    """Complete status of a batch job."""

    batch_id: str
    status: str  # validating, in_progress, completed, failed, expired, cancelled
    progress: ProgressMetrics
    timing: TimeMetrics
    output_file_id: Optional[str] = None
    error_file_id: Optional[str] = None
    errors: Optional[dict] = None

    @property
    def is_complete(self) -> bool:
        """Whether batch has finished processing (success or failure)."""
        return self.status in ("completed", "failed", "expired", "cancelled")

    @property
    def is_running(self) -> bool:
        """Whether batch is currently processing."""
        return self.status in ("validating", "in_progress")

    @property
    def completion_eta_seconds(self) -> Optional[float]:
        """Estimated seconds until completion."""
        if self.is_complete:
            return 0.0
        return self.timing.estimate_completion_seconds(self.progress)

    @property
    def status_emoji(self) -> str:
        """Emoji representing current status."""
        status_map = {
            "validating": "🔄",
            "in_progress": "⚙️",
            "completed": "✅",
            "failed": "❌",
            "expired": "⏰",
            "cancelled": "🚫",
        }
        return status_map.get(self.status, "❓")
