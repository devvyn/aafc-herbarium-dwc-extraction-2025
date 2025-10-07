"""
Flask Web Application for Batch Monitoring

Provides browser-based dashboard with real-time updates via SSE.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Generator

from flask import Flask, Response, render_template, request

from ..engine import BatchMonitorEngine


def create_app(history_file: Path = None) -> Flask:
    """
    Create and configure Flask application.

    Args:
        history_file: Optional path to batch history file

    Returns:
        Configured Flask app
    """
    app = Flask(__name__)
    engine = BatchMonitorEngine(history_file=history_file)

    @app.route("/")
    def index():
        """Render main dashboard page."""
        return render_template("dashboard.html")

    @app.route("/api/batches")
    def get_batches():
        """Get list of active batch IDs."""
        batch_ids = engine.get_active_batches()
        return {"batch_ids": batch_ids, "count": len(batch_ids)}

    @app.route("/api/status/<batch_id>")
    def get_status(batch_id: str):
        """Get current status for a specific batch."""
        try:
            status = engine.fetch_status(batch_id)
            return {
                "batch_id": status.batch_id,
                "status": status.status,
                "status_emoji": status.status_emoji,
                "is_complete": status.is_complete,
                "is_running": status.is_running,
                "progress": {
                    "total": status.progress.total,
                    "completed": status.progress.completed,
                    "failed": status.progress.failed,
                    "completion_percentage": status.progress.completion_percentage,
                },
                "timing": {
                    "elapsed_minutes": status.timing.elapsed_minutes,
                    "completion_eta_seconds": status.completion_eta_seconds,
                },
                "output_file_id": status.output_file_id,
            }
        except Exception as e:
            return {"error": str(e)}, 500

    @app.route("/stream")
    def stream():
        """
        Server-Sent Events stream for real-time updates.

        Query params:
            batch_ids: Comma-separated list of batch IDs to monitor
            refresh: Refresh interval in seconds (default: 30)
        """
        batch_ids = request.args.get("batch_ids", "").split(",")
        batch_ids = [bid.strip() for bid in batch_ids if bid.strip()]
        refresh_interval = int(request.args.get("refresh", 30))

        if not batch_ids:
            # Auto-discover
            batch_ids = engine.get_active_batches()

        def generate() -> Generator[str, None, None]:
            """Generate SSE data stream."""
            while True:
                try:
                    # Fetch statuses
                    statuses = engine.fetch_multiple(batch_ids)

                    # Convert to JSON-serializable format
                    data = {
                        "timestamp": datetime.now().isoformat(),
                        "batches": [
                            {
                                "batch_id": s.batch_id,
                                "status": s.status,
                                "status_emoji": s.status_emoji,
                                "is_complete": s.is_complete,
                                "progress": {
                                    "total": s.progress.total,
                                    "completed": s.progress.completed,
                                    "failed": s.progress.failed,
                                    "percentage": s.progress.completion_percentage,
                                },
                                "timing": {
                                    "elapsed_minutes": s.timing.elapsed_minutes,
                                    "eta_seconds": s.completion_eta_seconds,
                                },
                                "output_file_id": s.output_file_id,
                            }
                            for s in statuses
                        ],
                    }

                    # Send SSE message
                    yield f"data: {json.dumps(data)}\n\n"

                    # Check if all complete
                    if all(s.is_complete for s in statuses):
                        # Send completion message
                        yield f'data: {{"complete": true}}\n\n'
                        break

                    # Wait before next update
                    time.sleep(refresh_interval)

                except Exception as e:
                    # Send error message
                    yield f'data: {{"error": "{str(e)}"}}\n\n'
                    break

        return Response(generate(), mimetype="text/event-stream")

    return app
