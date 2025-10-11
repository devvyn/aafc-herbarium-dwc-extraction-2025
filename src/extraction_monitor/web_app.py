"""
Flask Web Application for Extraction Monitoring

Provides browser-based dashboard with SSE updates.
Matches TUI layout for consistent UX.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Generator

from flask import Flask, Response, render_template, request

from .engine import ExtractionMonitorEngine


def create_app() -> Flask:
    """
    Create and configure Flask application.

    Returns:
        Configured Flask app
    """
    app = Flask(__name__, template_folder="../../templates")
    engine = ExtractionMonitorEngine()

    @app.route("/")
    def index():
        """Render main dashboard page."""
        return render_template("extraction_dashboard.html")

    @app.route("/api/runs")
    def get_runs():
        """Get list of all extraction runs."""
        runs = engine.get_all_runs()
        return {
            "runs": [
                {"name": run.name, "path": str(run), "modified": run.stat().st_mtime}
                for run in runs
            ],
            "count": len(runs),
        }

    @app.route("/api/stats")
    def get_stats():
        """Get current stats for latest or specified run."""
        run_dir_str = request.args.get("run_dir")

        if run_dir_str:
            run_dir = Path(run_dir_str)
        else:
            run_dir = engine.find_latest_run()

        if not run_dir or not run_dir.exists():
            return {"error": "No extraction runs found"}, 404

        try:
            stats = engine.read_extraction_stats(run_dir)
            return {
                "run_id": stats.run_id,
                "model_name": stats.model_name,
                "total_specimens": stats.total_specimens,
                "completed": stats.completed,
                "failed": stats.failed,
                "successful": stats.completed - stats.failed,
                "success_rate": stats.success_rate,
                "field_stats": stats.field_stats,
                "latest_events": [
                    {
                        "specimen_id": event.get("image", "unknown"),
                        "success": "dwc" in event and event.get("dwc"),
                        "fields_extracted": len(event.get("dwc", {})),
                        "error": event.get("error"),
                        "timestamp": event.get("timestamp"),
                    }
                    for event in stats.latest_events
                ],
                "elapsed_seconds": stats.elapsed_seconds,
                "throughput": stats.throughput,
            }
        except Exception as e:
            return {"error": str(e)}, 500

    @app.route("/stream")
    def stream():
        """
        Server-Sent Events stream for real-time updates.

        Query params:
            run_dir: Path to run directory (default: latest)
            refresh: Refresh interval in seconds (default: 5)
        """
        run_dir_str = request.args.get("run_dir")
        refresh_interval = int(request.args.get("refresh", 5))

        if run_dir_str:
            run_dir = Path(run_dir_str)
        else:
            run_dir = engine.find_latest_run()

        if not run_dir:

            def error_stream():
                yield f'data: {json.dumps({"error": "No extraction runs found"})}\n\n'

            return Response(error_stream(), mimetype="text/event-stream")

        def generate() -> Generator[str, None, None]:
            """Generate SSE data stream."""
            while True:
                try:
                    stats = engine.read_extraction_stats(run_dir)

                    data = {
                        "timestamp": datetime.now().isoformat(),
                        "run_id": stats.run_id,
                        "model_name": stats.model_name,
                        "total_specimens": stats.total_specimens,
                        "completed": stats.completed,
                        "failed": stats.failed,
                        "successful": stats.completed - stats.failed,
                        "success_rate": stats.success_rate,
                        "completion_percentage": (
                            (stats.completed / stats.total_specimens * 100)
                            if stats.total_specimens > 0
                            else 0
                        ),
                        "field_stats": dict(
                            sorted(stats.field_stats.items(), key=lambda x: x[1], reverse=True)[:10]
                        ),  # Top 10
                        "latest_events": [
                            {
                                "specimen_id": event.get("image", "unknown")[:40],
                                "success": "dwc" in event and event.get("dwc"),
                                "fields_extracted": len(event.get("dwc", {})),
                                "error": event.get("error", "")[:50],
                            }
                            for event in reversed(
                                stats.latest_events[-15:]
                            )  # Last 15, newest first
                        ],
                        "elapsed_seconds": stats.elapsed_seconds,
                        "throughput": stats.throughput,
                        "is_complete": (
                            stats.completed >= stats.total_specimens and stats.total_specimens > 0
                        ),
                    }

                    # Send SSE message
                    yield f"data: {json.dumps(data)}\n\n"

                    # Check if complete
                    if data["is_complete"]:
                        yield 'data: {"complete": true}\n\n'
                        break

                    # Wait before next update
                    time.sleep(refresh_interval)

                except Exception as e:
                    # Send error message
                    yield f'data: {{"error": "{str(e)}"}}\n\n'
                    break

        return Response(generate(), mimetype="text/event-stream")

    return app
