#!/usr/bin/env python3
"""
Textual TUI for Real-Time Extraction Monitoring

Beautiful terminal interface with live updates from event bus.
Designed for tmux integration and long-running monitoring.

Usage:
    python scripts/monitor_tui.py --run-dir full_dataset_processing/openrouter_run_20251010_115131

Tmux integration:
    tmux split-window -h "python scripts/monitor_tui.py --run-dir <dir>"
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static
from textual.timer import Timer


class StatsCard(Static):
    """A card displaying a single stat."""

    def __init__(self, label: str, value: str = "0", emoji: str = "📊", color: str = "cyan"):
        super().__init__()
        self.label = label
        self.value_text = value
        self.emoji = emoji
        self.color = color

    def render(self) -> RenderableType:
        text = Text()
        text.append(f"{self.emoji} ", style="bold")
        text.append(f"{self.label}\n", style="dim")
        text.append(self.value_text, style=f"bold {self.color}")
        return Panel(text, border_style=self.color)

    def update_value(self, value: str):
        self.value_text = value
        self.refresh()


class ProgressCard(Static):
    """Main progress card with bar and metrics."""

    progress_pct: reactive[float] = reactive(0.0)
    completed: reactive[int] = reactive(0)
    total: reactive[int] = reactive(0)
    status: reactive[str] = reactive("INITIALIZING")

    def render(self) -> RenderableType:
        # Status indicator
        status_color = {"RUNNING": "green", "COMPLETE": "blue", "ERROR": "red"}.get(
            self.status, "yellow"
        )
        status_text = Text(f"● {self.status}", style=f"bold {status_color}")

        # Progress bar
        filled = int(self.progress_pct / 2)  # Scale to 50 chars
        bar = "█" * filled + "░" * (50 - filled)
        progress_text = Text(f"\n{bar}\n", style="cyan")
        progress_text.append(f"{self.completed} / {self.total} specimens ", style="bold white")
        progress_text.append(f"({self.progress_pct:.1f}%)", style="dim")

        content = Text.assemble(status_text, progress_text)
        return Panel(content, title="[bold]Extraction Progress", border_style="cyan")


class EventStreamWidget(Static):
    """Live scrolling event stream."""

    events: reactive[list] = reactive(list, init=False)

    def __init__(self):
        super().__init__()
        self.events = []

    def render(self) -> RenderableType:
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Status", width=3)
        table.add_column("Specimen", width=20)
        table.add_column("Details", width=40)
        table.add_column("Time", width=8)

        # Show last 15 events
        for event in self.events[-15:]:
            status_emoji = "✅" if event["success"] else "❌"
            status_style = "green" if event["success"] else "red"

            specimen_id = event["specimen_id"][:20]
            details = event["details"]
            time_str = event["time"]

            table.add_row(
                Text(status_emoji, style=status_style),
                Text(specimen_id, style="cyan"),
                Text(details, style="white" if event["success"] else "red"),
                Text(time_str, style="dim"),
            )

        return Panel(table, title="[bold]🔴 Live Event Stream", border_style="blue", height=20)

    def add_event(self, event: dict):
        self.events = self.events + [event]  # Trigger reactive update


class FieldQualityWidget(Static):
    """Field extraction quality bars."""

    field_stats: reactive[dict] = reactive(dict, init=False)

    def __init__(self):
        super().__init__()
        self.field_stats = {}

    def render(self) -> RenderableType:
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Field", width=25)
        table.add_column("Quality", width=30)
        table.add_column("%", width=6, justify="right")

        # Sort by extraction rate
        sorted_fields = sorted(self.field_stats.items(), key=lambda x: x[1], reverse=True)

        for field, rate in sorted_fields[:10]:  # Top 10 fields
            filled = int(rate / 5)  # Scale to 20 chars
            bar = "█" * filled + "░" * (20 - filled)

            # Color based on quality
            if rate >= 90:
                color = "green"
            elif rate >= 70:
                color = "yellow"
            else:
                color = "red"

            table.add_row(
                Text(field, style="cyan"),
                Text(bar, style=color),
                Text(f"{rate:.0f}%", style=f"bold {color}"),
            )

        return Panel(
            table, title="[bold]🎯 Field Extraction Quality", border_style="magenta", height=20
        )


class ExtractionMonitorApp(App):
    """Textual app for monitoring extraction progress."""

    CSS = """
    Screen {
        background: $surface;
    }

    #stats_row {
        height: 5;
        margin: 1;
    }

    #progress_card {
        height: 7;
        margin: 1;
    }

    #main_panels {
        height: 1fr;
        margin: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
    ]

    def __init__(self, run_dir: Path):
        super().__init__()
        self.run_dir = run_dir
        self.raw_jsonl = run_dir / "raw.jsonl"
        self.events_jsonl = run_dir / "events.jsonl"
        self.environment_json = run_dir / "environment.json"

        # Stats
        self.total_specimens = 0
        self.completed_count = 0
        self.failed_count = 0
        self.field_stats = {}

        self.update_timer: Optional[Timer] = None

    def compose(self) -> ComposeResult:
        yield Header()

        # Stats cards row
        with Horizontal(id="stats_row"):
            yield StatsCard("Total", "0", "📊", "blue")
            yield StatsCard("Completed", "0", "✅", "green")
            yield StatsCard("Success Rate", "0%", "📈", "magenta")
            yield StatsCard("Failed", "0", "❌", "red")

        # Progress card
        yield ProgressCard(id="progress_card")

        # Main panels
        with Horizontal(id="main_panels"):
            yield EventStreamWidget()
            yield FieldQualityWidget()

        yield Footer()

    def on_mount(self) -> None:
        """Start the update timer when app mounts."""
        self.title = f"🌿 Herbarium Monitor: {self.run_dir.name}"
        self.update_timer = self.set_interval(2.0, self.update_data)
        self.update_data()  # Initial load

    def update_data(self) -> None:
        """Read latest data from files and update widgets."""
        try:
            # Read environment.json for metadata
            if self.environment_json.exists():
                with open(self.environment_json) as f:
                    env_data = json.load(f)
                    self.total_specimens = env_data.get("total_specimens", 0)

            # Read raw.jsonl for extraction results
            if self.raw_jsonl.exists():
                results = []
                with open(self.raw_jsonl) as f:
                    for line in f:
                        if line.strip():
                            results.append(json.loads(line))

                self.completed_count = len(results)
                self.failed_count = sum(1 for r in results if "error" in r)
                successful_count = self.completed_count - self.failed_count

                # Calculate field extraction rates
                field_counts = {}
                for result in results:
                    if "dwc" in result:
                        for field in result["dwc"].keys():
                            field_counts[field] = field_counts.get(field, 0) + 1

                # Calculate percentages
                if successful_count > 0:
                    self.field_stats = {
                        field: (count / successful_count) * 100
                        for field, count in field_counts.items()
                    }

                # Update widgets
                self.update_stats_cards(successful_count)
                self.update_progress_card()
                self.update_field_quality()

                # Add latest event to stream
                if results:
                    latest = results[-1]
                    self.add_event_from_result(latest)

        except Exception as e:
            self.notify(f"Error updating data: {e}", severity="error")

    def update_stats_cards(self, successful_count: int):
        """Update the stats cards."""
        cards = self.query(StatsCard)
        if len(cards) >= 4:
            cards[0].update_value(f"{self.total_specimens:,}")
            cards[1].update_value(f"{self.completed_count:,}")

            success_rate = (
                (successful_count / self.completed_count * 100) if self.completed_count > 0 else 0
            )
            cards[2].update_value(f"{success_rate:.1f}%")
            cards[3].update_value(f"{self.failed_count:,}")

    def update_progress_card(self):
        """Update the progress card."""
        progress_card = self.query_one(ProgressCard)
        progress_card.completed = self.completed_count
        progress_card.total = self.total_specimens
        progress_card.progress_pct = (
            (self.completed_count / self.total_specimens * 100) if self.total_specimens > 0 else 0
        )
        progress_card.status = (
            "COMPLETE"
            if self.completed_count >= self.total_specimens and self.total_specimens > 0
            else "RUNNING"
        )

    def update_field_quality(self):
        """Update field quality widget."""
        field_widget = self.query_one(FieldQualityWidget)
        field_widget.field_stats = self.field_stats

    def add_event_from_result(self, result: dict):
        """Add event to stream from extraction result."""
        event_widget = self.query_one(EventStreamWidget)

        is_success = "dwc" in result and result["dwc"]
        specimen_id = result.get("image", "unknown")

        if is_success:
            field_count = len(result["dwc"])
            details = f"{field_count} fields extracted"
        else:
            error = result.get("error", "Unknown error")
            details = f"Error: {error[:40]}"

        event = {
            "success": is_success,
            "specimen_id": specimen_id,
            "details": details,
            "time": datetime.now().strftime("%H:%M:%S"),
        }

        event_widget.add_event(event)

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark


def main():
    parser = argparse.ArgumentParser(description="Real-time TUI monitor for herbarium extraction")
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Extraction run directory (contains raw.jsonl, events.jsonl, environment.json)",
    )

    args = parser.parse_args()

    if not args.run_dir.exists():
        print(f"❌ Run directory not found: {args.run_dir}")
        return 1

    app = ExtractionMonitorApp(args.run_dir)
    app.run()


if __name__ == "__main__":
    main()
