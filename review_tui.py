from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List

from PIL import Image as PILImage
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import ListItem, ListView, Static

from io_utils.candidates import Candidate, Decision, fetch_candidates, record_decision

ASCII_CHARS = "@%#*+=-:. "


def _ascii_art(path: Path, width: int = 40) -> str:
    """Return a crude ASCII rendering of an image."""
    try:
        img = PILImage.open(path).convert("L")
        aspect_ratio = img.height / img.width
        height = max(1, int(width * aspect_ratio * 0.55))
        img = img.resize((width, height))
        pixels = list(img.getdata())
        chars = [ASCII_CHARS[p * len(ASCII_CHARS) // 256] for p in pixels]
        lines = ["".join(chars[i : i + width]) for i in range(0, len(chars), width)]
        return "\n".join(lines)
    except Exception:
        return f"[image not available: {path}]"


class ReviewApp(App[Decision | None]):
    """Textual app to review candidates alongside an image."""

    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, db_path: Path, image_name: str) -> None:
        super().__init__()
        self.db_path = db_path
        self.image_name = image_name
        self.conn = sqlite3.connect(db_path)
        self.candidates: List[Candidate] = fetch_candidates(self.conn, image_name)
        self.candidates.sort(key=lambda c: c.confidence, reverse=True)

    def compose(self) -> ComposeResult:
        if not self.candidates:
            yield Static(f"No candidates found for {self.image_name}")
            return
        img_widget = Static(_ascii_art(Path(self.image_name)))
        items = [
            ListItem(Static(f"{c.engine} ({c.confidence:.2f}): {c.value}"))
            for c in self.candidates
        ]
        list_view = ListView(*items)
        yield Horizontal(img_widget, list_view)

    def on_list_view_selected(self, event: ListView.Selected) -> None:  # noqa: D401
        """Persist the selected candidate and exit."""
        cand = self.candidates[event.index]
        decision = record_decision(self.conn, self.image_name, cand)
        self.conn.close()
        self.exit(decision)

    def action_quit(self) -> None:
        self.conn.close()
        self.exit(None)


def review_candidates_tui(db_path: Path, image: str) -> Decision | None:
    """Launch the Textual UI for candidate review."""
    return ReviewApp(db_path, image).run()


if __name__ == "__main__":
    raise SystemExit("Use 'python review.py --tui' to launch the text interface.")
