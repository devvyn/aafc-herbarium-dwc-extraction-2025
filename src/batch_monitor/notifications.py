"""
Desktop Notifications for Batch Monitoring

Sends native macOS notifications when batches complete.
"""

import subprocess
from typing import Optional

from .models import BatchStatus


class NotificationManager:
    """Manager for desktop notifications."""

    def __init__(self, enabled: bool = True):
        """
        Initialize notification manager.

        Args:
            enabled: Whether notifications are enabled
        """
        self.enabled = enabled

    def notify_completion(self, status: BatchStatus):
        """
        Send notification when batch completes.

        Args:
            status: Completed batch status
        """
        if not self.enabled:
            return

        # Determine notification content based on status
        if status.status == "completed":
            title = f"{status.status_emoji} Batch Complete"
            message = (
                f"Successfully processed {status.progress.completed}/{status.progress.total} requests\n"
                f"Time: {status.timing.elapsed_minutes:.1f} min"
            )
            if status.progress.failed > 0:
                message += f"\n⚠️ {status.progress.failed} failed"
        elif status.status == "failed":
            title = f"{status.status_emoji} Batch Failed"
            message = (
                f"Batch {status.batch_id[:16]} failed after {status.timing.elapsed_minutes:.1f} min"
            )
        elif status.status == "expired":
            title = f"{status.status_emoji} Batch Expired"
            message = f"Batch {status.batch_id[:16]} expired without completing"
        elif status.status == "cancelled":
            title = f"{status.status_emoji} Batch Cancelled"
            message = f"Batch {status.batch_id[:16]} was cancelled"
        else:
            # Unknown status, don't notify
            return

        self._send_macos_notification(title, message, status.batch_id[:16])

    def notify_progress(
        self, status: BatchStatus, threshold: float = 0.5, last_notified: Optional[float] = None
    ):
        """
        Send notification at progress milestones (50%, 75%, etc.).

        Args:
            status: Current batch status
            threshold: Progress threshold to notify at (0.0-1.0)
            last_notified: Last notified threshold (to avoid duplicates)

        Returns:
            Updated last_notified value
        """
        if not self.enabled or not status.is_running:
            return last_notified

        current_progress = status.progress.completion_rate

        # Check if we've crossed a threshold
        if current_progress >= threshold and (last_notified is None or last_notified < threshold):
            title = f"⚙️ Batch Progress: {int(threshold * 100)}%"
            message = (
                f"{status.progress.completed}/{status.progress.total} requests completed\n"
                f"Time: {status.timing.elapsed_minutes:.1f} min"
            )
            if status.completion_eta_seconds:
                message += f"\nETA: ~{status.completion_eta_seconds / 60:.1f} min"

            self._send_macos_notification(title, message, status.batch_id[:16])
            return threshold

        return last_notified

    def _send_macos_notification(self, title: str, message: str, subtitle: str = ""):
        """
        Send native macOS notification using osascript.

        Args:
            title: Notification title
            message: Notification body
            subtitle: Optional subtitle
        """
        script = f"""
        display notification "{message}" ¬
            with title "{title}" ¬
            subtitle "{subtitle}" ¬
            sound name "Glass"
        """

        try:
            subprocess.run(
                ["osascript", "-e", script],
                check=True,
                capture_output=True,
                timeout=5,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            # Silently fail - notifications are nice-to-have
            pass
