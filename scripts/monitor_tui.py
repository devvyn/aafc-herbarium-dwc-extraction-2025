#!/usr/bin/env python3
"""
Textual TUI for Real-Time Extraction Monitoring

Beautiful terminal interface with live updates from event bus.
Designed for tmux integration and long-running monitoring.
With Tilly the Pekingese charm! 🐕

Usage:
    python scripts/monitor_tui.py --run-dir full_dataset_processing/openrouter_run_20251010_115131

Tmux integration:
    tmux split-window -h "python scripts/monitor_tui.py --run-dir <dir>"
"""

import argparse
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image
from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich_pixels import Pixels
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static
from textual.timer import Timer


# Tilly's encouraging quotes (Barkour cross-pollination!)
TILLY_QUOTES = [
    "🐕 This Rosa looks lovely!",
    "🐕 Great job on that Carex!",
    "🐕 Parkour through those specimens!",
    "🐕 You're climbing the taxonomy tree!",
    "🐕 Specimen hunting mission!",
    "🐕 That's a beautiful plant!",
    "🐕 Keep up the great work!",
    "🐕 Flora exploration in progress!",
]


def get_tilly_milestone_message(count: int) -> Optional[str]:
    """Get Tilly's milestone message for specimen count."""
    if count == 10:
        return "🐕 Tilly: Nice warm-up!"
    elif count == 50:
        return "🐕🥓 Tilly found bacon break!"
    elif count == 100:
        return "🐕⬆️💨 Tilly: Master curator level!"
    elif count == 250:
        return "🐕✨ Tilly: Parkour expert mode!"
    elif count == 500:
        return "🐕☁️ Tilly reached the clouds!"
    return None


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
    """Main progress card with bar and metrics - with Tilly's height indicator!"""

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

        # Tilly's height indicator (like Barkour climb!)
        progress_text.append(f"⬆️ {self.progress_pct:.1f}%", style="bold yellow")

        content = Text.assemble(status_text, progress_text)
        return Panel(content, title="[bold]🐕 Extraction Progress", border_style="cyan")


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


class SpecimenImageWidget(Static):
    """Inline specimen image preview using iTerm2/rich-pixels."""

    current_image_path: reactive[Optional[Path]] = reactive(None)
    specimen_id: reactive[str] = reactive("No specimen")

    def render(self) -> RenderableType:
        if self.current_image_path and self.current_image_path.exists():
            try:
                # Load and resize image for terminal display
                img = Image.open(self.current_image_path)
                img.thumbnail((60, 40))  # Terminal character size

                # Convert to rich-pixels
                pixels = Pixels.from_image(img)

                # Create renderable group with image and label
                from rich.console import Group

                content = Group(
                    pixels,
                    Text(),  # Spacer
                    Text(self.specimen_id, style="cyan bold", justify="center"),
                )

                return Panel(
                    content,
                    title="[bold]🔬 Current Specimen",
                    border_style="cyan",
                )
            except Exception as e:
                error_text = Text(f"Error loading image:\n{str(e)}", style="red")
                return Panel(error_text, title="[bold]🔬 Current Specimen", border_style="red")
        else:
            placeholder = Text("No image available\n\nWaiting for extraction...", style="dim")
            return Panel(placeholder, title="[bold]🔬 Current Specimen", border_style="dim")

    def update_image(self, image_path: Optional[Path], specimen_id: str):
        """Update the displayed image."""
        self.current_image_path = image_path
        self.specimen_id = specimen_id


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

    #left_column {
        width: 2fr;
    }

    #right_column {
        width: 1fr;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
    ]

    def __init__(self, run_dir: Path, image_dir: Optional[Path] = None):
        super().__init__()
        self.run_dir = run_dir
        self.raw_jsonl = run_dir / "raw.jsonl"
        self.events_jsonl = run_dir / "events.jsonl"
        # Support both old (environment.json) and new (manifest.json) formats
        self.manifest_json = run_dir / "manifest.json"
        self.environment_json = run_dir / "environment.json"

        # Image directory for inline previews
        self.image_dir = image_dir or Path.home() / "Documents/projects/AAFC/pyproj/resized"

        # Stats
        self.total_specimens = 0
        self.completed_count = 0
        self.failed_count = 0
        self.field_stats = {}
        self.current_specimen_id: Optional[str] = None

        # Tilly milestone tracking
        self.last_milestone = 0
        self.tilly_message_timer = 0

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

        # Main panels with 3-column layout
        with Horizontal(id="main_panels"):
            # Left: Event stream and field quality
            with Vertical(id="left_column"):
                yield EventStreamWidget()
                yield FieldQualityWidget()

            # Right: Specimen image preview
            with Vertical(id="right_column"):
                yield SpecimenImageWidget()

        yield Footer()

    def on_mount(self) -> None:
        """Start the update timer when app mounts."""
        self.title = f"🌿🐕 Herbarium Monitor: {self.run_dir.name}"
        self.update_timer = self.set_interval(2.0, self.update_data)
        self.update_data()  # Initial load

        # Show welcome message with random Tilly quote
        welcome_quote = random.choice(TILLY_QUOTES)
        self.notify(f"{welcome_quote} Let's review some plants!", timeout=5)

    def update_data(self) -> None:
        """Read latest data from files and update widgets."""
        try:
            # Read manifest.json or environment.json for metadata
            metadata_file = None
            if self.manifest_json.exists():
                metadata_file = self.manifest_json
            elif self.environment_json.exists():
                metadata_file = self.environment_json

            if metadata_file:
                with open(metadata_file) as f:
                    env_data = json.load(f)
                    # Try different formats for total specimens count
                    self.total_specimens = env_data.get("total_specimens", 0)
                    if self.total_specimens == 0:
                        # Try manifest config format
                        config = env_data.get("config", {})
                        self.total_specimens = config.get("total_specimens", 0)

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

                # If we don't have total from metadata, use completed count as estimate
                if self.total_specimens == 0:
                    self.total_specimens = self.completed_count

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

                # Check for Tilly milestones
                self.check_tilly_milestones(successful_count)

                # Add latest event to stream and update image
                if results:
                    latest = results[-1]
                    self.add_event_from_result(latest)
                    self.update_specimen_image(latest)

                    # Occasionally show Tilly encouragement (every 20 specimens)
                    if successful_count % 20 == 0 and successful_count > self.tilly_message_timer:
                        self.tilly_message_timer = successful_count
                        tilly_quote = random.choice(TILLY_QUOTES)
                        self.notify(tilly_quote, timeout=3)

        except Exception as e:
            self.notify(f"Error updating data: {e}", severity="error")

    def check_tilly_milestones(self, count: int):
        """Check if we hit a Tilly milestone and show celebration message."""
        milestone_msg = get_tilly_milestone_message(count)
        if milestone_msg and count > self.last_milestone:
            self.last_milestone = count
            self.notify(milestone_msg, severity="information", timeout=8)

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

    def update_specimen_image(self, result: dict):
        """Update the specimen image preview."""
        specimen_id = result.get("image", "unknown")

        # Skip if same specimen (avoid unnecessary updates)
        if specimen_id == self.current_specimen_id:
            return

        self.current_specimen_id = specimen_id

        # Find image in image directory
        image_path = self.image_dir / specimen_id
        if not image_path.exists():
            # Try common extensions
            for ext in [".JPG", ".jpg", ".jpeg", ".JPEG", ".png", ".PNG"]:
                test_path = self.image_dir / f"{specimen_id.rsplit('.', 1)[0]}{ext}"
                if test_path.exists():
                    image_path = test_path
                    break

        # Update widget
        image_widget = self.query_one(SpecimenImageWidget)
        if image_path.exists():
            image_widget.update_image(image_path, specimen_id)
        else:
            image_widget.update_image(None, specimen_id)

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
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=None,
        help="Directory containing specimen images (defaults to ~/Documents/projects/AAFC/pyproj/resized)",
    )

    args = parser.parse_args()

    if not args.run_dir.exists():
        print(f"❌ Run directory not found: {args.run_dir}")
        return 1

    app = ExtractionMonitorApp(args.run_dir, args.image_dir)
    app.run()


if __name__ == "__main__":
    main()
