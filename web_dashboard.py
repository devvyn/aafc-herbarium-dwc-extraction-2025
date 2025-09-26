#!/usr/bin/env python3
"""Modern web dashboard for herbarium OCR system."""

import json
import sqlite3
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from fastapi.responses import HTMLResponse, JSONResponse
    import uvicorn
except ImportError:
    print("❌ FastAPI required: pip install fastapi uvicorn jinja2")
    exit(1)

from io_utils.candidates import fetch_candidates_sqlite


@dataclass
class ProcessingStatus:
    """Real-time processing status."""
    total_images: int = 0
    processed: int = 0
    successful: int = 0
    failed: int = 0
    current_image: Optional[str] = None
    start_time: Optional[str] = None
    errors: List[str] = None
    engine_stats: Dict[str, int] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.engine_stats is None:
            self.engine_stats = {}


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


# Initialize FastAPI app
app = FastAPI(title="Herbarium OCR Dashboard", version="1.0.0")
templates = Jinja2Templates(directory="templates")
manager = WebSocketManager()

# Global state
processing_status = ProcessingStatus()


# Create templates directory and files
def create_templates():
    """Create template files if they don't exist."""
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)

    # Main dashboard template
    dashboard_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌿 Herbarium OCR Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        .gradient-bg {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        .processing-animation {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        .stat-card {
            transition: transform 0.2s ease-in-out;
        }
        .stat-card:hover {
            transform: translateY(-2px);
        }
    </style>
</head>
<body class="bg-gray-100" x-data="dashboard()">
    <!-- Header -->
    <header class="gradient-bg shadow-lg">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center py-6">
                <div class="flex items-center">
                    <h1 class="text-3xl font-bold text-white">🌿 Herbarium OCR</h1>
                    <span class="ml-4 px-3 py-1 bg-white bg-opacity-20 rounded-full text-white text-sm">
                        v1.0.0
                    </span>
                </div>
                <div class="flex items-center space-x-4">
                    <div class="text-white text-sm">
                        <span x-show="status.current_image" class="processing-animation">
                            🔄 Processing: <span x-text="status.current_image"></span>
                        </span>
                        <span x-show="!status.current_image">
                            ⏸️ Ready
                        </span>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        <!-- Stats Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <!-- Total Images -->
            <div class="stat-card bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="text-3xl">📊</div>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 truncate">Total Images</dt>
                                <dd class="text-3xl font-bold text-gray-900" x-text="status.total_images">0</dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Processed -->
            <div class="stat-card bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="text-3xl">✅</div>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 truncate">Processed</dt>
                                <dd class="text-3xl font-bold text-green-600" x-text="status.processed">0</dd>
                            </dl>
                        </div>
                    </div>
                    <div class="mt-2">
                        <div class="bg-gray-200 rounded-full h-2">
                            <div class="bg-green-500 h-2 rounded-full transition-all duration-300"
                                 :style="`width: ${status.total_images > 0 ? (status.processed / status.total_images * 100) : 0}%`"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Success Rate -->
            <div class="stat-card bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="text-3xl">📈</div>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 truncate">Success Rate</dt>
                                <dd class="text-3xl font-bold text-blue-600"
                                    x-text="status.processed > 0 ? Math.round(status.successful / status.processed * 100) + '%' : '0%'">0%</dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Failed -->
            <div class="stat-card bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="text-3xl">❌</div>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 truncate">Failed</dt>
                                <dd class="text-3xl font-bold text-red-600" x-text="status.failed">0</dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts and Details -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <!-- Engine Usage Chart -->
            <div class="bg-white shadow rounded-lg p-6">
                <h3 class="text-lg font-medium text-gray-900 mb-4">🤖 Engine Usage</h3>
                <canvas id="engineChart" width="400" height="200"></canvas>
            </div>

            <!-- Processing Timeline -->
            <div class="bg-white shadow rounded-lg p-6">
                <h3 class="text-lg font-medium text-gray-900 mb-4">⏱️ Processing Timeline</h3>
                <div x-show="status.start_time">
                    <p class="text-sm text-gray-600">Started: <span x-text="formatTime(status.start_time)"></span></p>
                    <p class="text-sm text-gray-600">Elapsed: <span x-text="getElapsedTime()"></span></p>
                    <p class="text-sm text-gray-600" x-show="status.processed > 0">
                        Rate: <span x-text="getProcessingRate()"></span> images/sec
                    </p>
                </div>
                <div x-show="!status.start_time" class="text-gray-500 text-center py-8">
                    No active processing session
                </div>
            </div>
        </div>

        <!-- Recent Activity -->
        <div class="bg-white shadow rounded-lg">
            <div class="px-6 py-4 border-b border-gray-200">
                <h3 class="text-lg font-medium text-gray-900">📋 Recent Activity</h3>
            </div>
            <div class="px-6 py-4">
                <div class="flow-root">
                    <ul class="-mb-8">
                        <template x-for="(error, index) in status.errors.slice(-5)" :key="index">
                            <li class="relative pb-8">
                                <div class="flex items-start space-x-3">
                                    <div class="flex-shrink-0">
                                        <div class="h-8 w-8 rounded-full bg-red-100 flex items-center justify-center">
                                            <span class="text-red-500 text-sm">❌</span>
                                        </div>
                                    </div>
                                    <div class="min-w-0 flex-1">
                                        <div>
                                            <p class="text-sm text-gray-900" x-text="error"></p>
                                            <p class="text-xs text-gray-500" x-text="formatTime(new Date().toISOString())"></p>
                                        </div>
                                    </div>
                                </div>
                            </li>
                        </template>
                        <div x-show="status.errors.length === 0" class="text-center py-8 text-gray-500">
                            No recent errors
                        </div>
                    </ul>
                </div>
            </div>
        </div>
    </main>

    <script>
        function dashboard() {
            return {
                status: {
                    total_images: 0,
                    processed: 0,
                    successful: 0,
                    failed: 0,
                    current_image: null,
                    start_time: null,
                    errors: [],
                    engine_stats: {}
                },
                chart: null,

                init() {
                    this.connectWebSocket();
                    this.initChart();
                },

                connectWebSocket() {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

                    ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        this.status = { ...this.status, ...data };
                        this.updateChart();
                    };

                    ws.onclose = () => {
                        console.log('WebSocket connection closed. Attempting to reconnect...');
                        setTimeout(() => this.connectWebSocket(), 3000);
                    };
                },

                initChart() {
                    const ctx = document.getElementById('engineChart').getContext('2d');
                    this.chart = new Chart(ctx, {
                        type: 'doughnut',
                        data: {
                            labels: [],
                            datasets: [{
                                data: [],
                                backgroundColor: [
                                    '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'
                                ]
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    position: 'bottom'
                                }
                            }
                        }
                    });
                },

                updateChart() {
                    if (!this.chart) return;

                    const engines = Object.keys(this.status.engine_stats);
                    const counts = Object.values(this.status.engine_stats);

                    this.chart.data.labels = engines;
                    this.chart.data.datasets[0].data = counts;
                    this.chart.update();
                },

                formatTime(isoString) {
                    if (!isoString) return '';
                    return new Date(isoString).toLocaleTimeString();
                },

                getElapsedTime() {
                    if (!this.status.start_time) return '';
                    const start = new Date(this.status.start_time);
                    const now = new Date();
                    const elapsed = Math.floor((now - start) / 1000);

                    const hours = Math.floor(elapsed / 3600);
                    const minutes = Math.floor((elapsed % 3600) / 60);
                    const seconds = elapsed % 60;

                    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                },

                getProcessingRate() {
                    if (!this.status.start_time || this.status.processed === 0) return '0';
                    const start = new Date(this.status.start_time);
                    const now = new Date();
                    const elapsed = (now - start) / 1000;

                    const rate = this.status.processed / elapsed;
                    return rate.toFixed(1);
                }
            }
        }
    </script>
</body>
</html>'''

    with open(templates_dir / "dashboard.html", "w") as f:
        f.write(dashboard_html)


@app.on_event("startup")
async def startup_event():
    """Initialize templates on startup."""
    create_templates()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        # Send initial status
        await websocket.send_json(asdict(processing_status))

        while True:
            # Keep connection alive and handle incoming messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/api/status")
async def get_status():
    """Get current processing status."""
    return JSONResponse(asdict(processing_status))


@app.post("/api/start-processing")
async def start_processing(config: Dict[str, Any]):
    """Start processing with given configuration."""
    global processing_status

    processing_status.start_time = datetime.now().isoformat()
    processing_status.total_images = config.get("total_images", 0)
    processing_status.processed = 0
    processing_status.successful = 0
    processing_status.failed = 0
    processing_status.current_image = None
    processing_status.errors = []
    processing_status.engine_stats = {}

    # Broadcast update
    await manager.broadcast(asdict(processing_status))

    return {"status": "started"}


@app.post("/api/update-progress")
async def update_progress(update: Dict[str, Any]):
    """Update processing progress."""
    global processing_status

    # Update status fields
    for key, value in update.items():
        if hasattr(processing_status, key):
            setattr(processing_status, key, value)

    # Broadcast update
    await manager.broadcast(asdict(processing_status))

    return {"status": "updated"}


@app.get("/api/results/{db_path:path}")
async def get_results(db_path: str):
    """Get processing results from database."""
    db_file = Path(db_path)
    if not db_file.exists():
        raise HTTPException(status_code=404, detail="Database not found")

    try:
        with sqlite3.connect(db_file) as conn:
            # Get summary statistics
            cursor = conn.cursor()

            # Total candidates
            cursor.execute("SELECT COUNT(*) FROM candidates")
            total_candidates = cursor.fetchone()[0]

            # Engine breakdown
            cursor.execute("SELECT engine, COUNT(*) FROM candidates GROUP BY engine ORDER BY COUNT(*) DESC")
            engines = dict(cursor.fetchall())

            # Average confidence by engine
            cursor.execute("SELECT engine, AVG(confidence) FROM candidates GROUP BY engine")
            avg_confidence = dict(cursor.fetchall())

            # Recent candidates
            cursor.execute("""
                SELECT image, value, engine, confidence, error
                FROM candidates
                ORDER BY rowid DESC
                LIMIT 10
            """)
            recent = [
                {
                    "image": row[0],
                    "value": row[1][:100] + "..." if len(row[1]) > 100 else row[1],
                    "engine": row[2],
                    "confidence": row[3],
                    "error": bool(row[4])
                }
                for row in cursor.fetchall()
            ]

            return {
                "total_candidates": total_candidates,
                "engines": engines,
                "avg_confidence": avg_confidence,
                "recent_candidates": recent
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/images")
async def list_images():
    """List available image sets for processing."""
    image_dirs = []

    # Look for common image directories
    for pattern in ["images", "trial_images", "*_images", "specimens"]:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                image_count = len(list(path.glob("*.jpg")) + list(path.glob("*.png")))
                if image_count > 0:
                    image_dirs.append({
                        "path": str(path),
                        "name": path.name,
                        "image_count": image_count,
                        "modified": path.stat().st_mtime
                    })

    return {"image_directories": sorted(image_dirs, key=lambda x: x["modified"], reverse=True)}


async def run_dashboard(host: str = "0.0.0.0", port: int = 8000):
    """Run the web dashboard server."""
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


def main():
    """Main entry point for web dashboard."""
    import argparse

    parser = argparse.ArgumentParser(description="Herbarium OCR Web Dashboard")
    parser.add_argument("--host", default="0.0.0.0", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")

    args = parser.parse_args()

    print(f"🌐 Starting Herbarium OCR Dashboard on http://{args.host}:{args.port}")
    print("📊 Real-time processing updates and result visualization")

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
