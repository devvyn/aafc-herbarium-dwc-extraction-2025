from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List
from urllib.parse import parse_qs, unquote

from io_utils.candidates import Candidate, Decision, fetch_candidates_sqlite, record_decision


def get_commit_hash() -> str:
    """Return the current Git commit hash."""
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def get_export_version(db_path: Path) -> str:
    """Read export version from a sibling text file if available."""
    version_file = db_path.parent / "export_version.txt"
    return version_file.read_text().strip() if version_file.exists() else "unknown"


class ReviewServer(ThreadingHTTPServer):
    """HTTP server carrying database and metadata context."""

    def __init__(self, addr: tuple[str, int], handler: type[BaseHTTPRequestHandler], **ctx):
        super().__init__(addr, handler)
        self.ctx = ctx


class ReviewHandler(BaseHTTPRequestHandler):
    server: ReviewServer

    def _send_headers(self, status: int, content_type: str = "text/html") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("X-Commit-Hash", self.server.ctx["commit"])
        self.send_header("X-Export-Version", self.server.ctx["export"])
        self.end_headers()

    def _render_template(self, body: str) -> bytes:
        footer = f"<footer>commit: {self.server.ctx['commit']} | export: {self.server.ctx['export']}</footer>"
        html = f"<html><body>{body}{footer}</body></html>"
        return html.encode()

    # Routing helpers -------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802
        path = unquote(self.path)
        if path == "/":
            self._serve_index()
        elif path.startswith("/review/"):
            self._serve_review(path.split("/", 2)[2])
        elif path.startswith("/images/"):
            self._serve_image(path.split("/", 2)[2])
        elif path.startswith("/candidates/"):
            self._serve_candidates(path.split("/", 2)[2])
        else:
            self._send_headers(404)

    def do_POST(self) -> None:  # noqa: N802
        path = unquote(self.path)
        if path == "/decision":
            self._save_decision()
        else:
            self._send_headers(404)

    # GET handlers ----------------------------------------------------
    def _serve_index(self) -> None:
        conn: sqlite3.Connection = self.server.ctx["conn"]
        rows = conn.execute("SELECT DISTINCT image FROM candidates ORDER BY image").fetchall()
        links = "".join(f'<li><a href="/review/{row[0]}">{row[0]}</a></li>' for row in rows)
        body = f"<h1>Images</h1><ul>{links}</ul>"
        self._send_headers(200)
        self.wfile.write(self._render_template(body))

    def _serve_review(self, image: str) -> None:
        conn: sqlite3.Connection = self.server.ctx["conn"]
        cands: List[Candidate] = fetch_candidates_sqlite(conn, image)
        options = "".join(
            f'<label><input type="radio" name="candidate" value="{c.engine}|{c.value}">'  # noqa: E501
            f"{c.engine} ({c.confidence:.2f}): {c.value}</label><br>"
            for c in cands
        )
        form = (
            f"<h1>{image}</h1>"
            f'<img src="/images/{image}" style="max-width:100%">'
            f'<form method="post" action="/decision">'
            f'<input type="hidden" name="image" value="{image}">{options}'
            '<button type="submit">Save</button></form>'
        )
        self._send_headers(200)
        self.wfile.write(self._render_template(form))

    def _serve_image(self, name: str) -> None:
        images_root = self.server.ctx["images"].resolve()
        img_path = (images_root / name).resolve()
        if not img_path.is_file() or not img_path.is_relative_to(images_root):
            self._send_headers(404)
            return
        data = img_path.read_bytes()
        content_type = "image/jpeg" if name.lower().endswith(".jpg") else "application/octet-stream"
        self._send_headers(200, content_type)
        self.wfile.write(data)

    def _serve_candidates(self, image: str) -> None:
        conn: sqlite3.Connection = self.server.ctx["conn"]
        cands = fetch_candidates_sqlite(conn, image)
        payload: Dict[str, object] = {
            "image": image,
            "candidates": [c.model_dump() for c in cands],
            "metadata": self.server.ctx["metadata"],
        }
        body = json.dumps(payload).encode()
        self._send_headers(200, "application/json")
        self.wfile.write(body)

    # POST handlers ---------------------------------------------------
    def _save_decision(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(length).decode()
        params = parse_qs(data)
        image = params.get("image", [""])[0]
        choice = params.get("candidate", [""])[0]
        engine, value = choice.split("|", 1) if "|" in choice else ("", "")
        conn: sqlite3.Connection = self.server.ctx["conn"]
        cands = fetch_candidates_sqlite(conn, image)
        match = next((c for c in cands if c.value == value and c.engine == engine), None)
        if not match:
            self._send_headers(404, "application/json")
            self.wfile.write(
                json.dumps(
                    {"error": "candidate not found", "metadata": self.server.ctx["metadata"]}
                ).encode()
            )
            return
        decision: Decision = record_decision(conn, image, match)
        payload = {"decision": decision.model_dump(), "metadata": self.server.ctx["metadata"]}
        self._send_headers(200, "application/json")
        self.wfile.write(json.dumps(payload).encode())


def main() -> None:
    parser = argparse.ArgumentParser(description="Web review interface")
    parser.add_argument(
        "--db", type=Path, default=Path("output/candidates.db"), help="Path to candidates database"
    )
    parser.add_argument(
        "--images", type=Path, default=Path("output"), help="Directory containing images"
    )
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the web server")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db, check_same_thread=False)
    commit_hash = get_commit_hash()
    export_version = get_export_version(args.db)
    metadata = {"commit": commit_hash, "export": export_version}
    server = ReviewServer(
        ("0.0.0.0", args.port),
        ReviewHandler,
        conn=conn,
        images=args.images,
        commit=commit_hash,
        export=export_version,
        metadata=metadata,
    )
    print(f"Serving on http://localhost:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        conn.close()


if __name__ == "__main__":
    main()
