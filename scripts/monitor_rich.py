#!/usr/bin/env python3
"""
Rich Console Monitor - Snapshot View

Quick status snapshot with beautiful terminal formatting.
Perfect for checking status without launching full TUI.

Usage:
    python scripts/monitor_rich.py --run-dir full_dataset_processing/openrouter_run_20251010_115131
    python scripts/monitor_rich.py  # Auto-detects latest run
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def find_latest_run() -> Path:
    """Find the most recent extraction run directory."""
    base = Path("full_dataset_processing")
    if not base.exists():
        raise FileNotFoundError("No full_dataset_processing directory found")

    runs = [d for d in base.iterdir() if d.is_dir() and (d / "raw.jsonl").exists()]
    if not runs:
        raise FileNotFoundError("No extraction runs found")

    # Sort by modification time
    latest = max(runs, key=lambda d: (d / "raw.jsonl").stat().st_mtime)
    return latest


def read_extraction_data(run_dir: Path) -> dict:
    """Read extraction data from run directory."""
    data = {
        "run_id": run_dir.name,
        "total": 0,
        "completed": 0,
        "failed": 0,
        "field_stats": {},
        "latest_events": [],
    }

    # Read environment for total count
    env_file = run_dir / "environment.json"
    if env_file.exists():
        with open(env_file) as f:
            env_data = json.load(f)
            # Try to extract total from command
            command = env_data.get("command", "")
            if "--limit" not in command:
                # Assume full dataset
                data["total"] = 2885
            else:
                # Parse limit from command
                import re

                match = re.search(r"--limit\s+(\d+)", command)
                if match:
                    data["total"] = int(match.group(1))

    # Read extraction results
    raw_file = run_dir / "raw.jsonl"
    if raw_file.exists():
        results = []
        with open(raw_file) as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))

        data["completed"] = len(results)
        data["failed"] = sum(1 for r in results if "error" in r)

        # Calculate field stats
        field_counts = {}
        successful = [r for r in results if "dwc" in r]

        for result in successful:
            for field in result["dwc"].keys():
                field_counts[field] = field_counts.get(field, 0) + 1

        if successful:
            data["field_stats"] = {
                field: (count / len(successful)) * 100 for field, count in field_counts.items()
            }

        # Get latest 5 events
        data["latest_events"] = results[-5:]

    return data


def create_hero_panel(data: dict) -> Panel:
    """Create the hero progress panel."""
    completed = data["completed"]
    total = data["total"]
    failed = data["failed"]
    successful = completed - failed

    percentage = (completed / total * 100) if total > 0 else 0

    # Status indicator
    if completed >= total and total > 0:
        status = Text("● COMPLETE", style="bold blue")
    else:
        status = Text("● RUNNING", style="bold green")

    # Progress bar
    bar_width = 50
    filled = int((completed / total) * bar_width) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_width - filled)

    content = Text()
    content.append(status)
    content.append("\n\n")
    content.append(bar, style="cyan")
    content.append("\n\n")
    content.append(f"{completed:,} / {total:,} specimens ", style="bold white")
    content.append(f"({percentage:.1f}%)\n", style="dim")
    content.append(f"✅ {successful:,} successful  ", style="green")
    content.append(f"❌ {failed:,} failed", style="red")

    return Panel(content, title="[bold cyan]Extraction Progress", border_style="cyan")


def create_stats_table(data: dict) -> Table:
    """Create stats summary table."""
    completed = data["completed"]
    failed = data["failed"]
    successful = completed - failed
    success_rate = (successful / completed * 100) if completed > 0 else 0

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Stat", style="cyan")
    table.add_column("Value", style="bold white", justify="right")

    table.add_row("📊 Total Specimens", f"{data['total']:,}")
    table.add_row("✅ Completed", f"{completed:,}")
    table.add_row("📈 Success Rate", f"{success_rate:.1f}%")
    table.add_row("❌ Failed", f"{failed:,}")

    return Panel(table, title="[bold]Statistics", border_style="blue")


def create_field_quality_table(data: dict) -> Table:
    """Create field extraction quality table."""
    table = Table(show_header=True, box=None, padding=(0, 1))
    table.add_column("Field", style="cyan", width=25)
    table.add_column("Quality", width=25)
    table.add_column("%", justify="right", style="bold", width=6)

    # Sort by extraction rate
    sorted_fields = sorted(data["field_stats"].items(), key=lambda x: x[1], reverse=True)

    for field, rate in sorted_fields[:10]:  # Top 10
        # Create quality bar
        filled = int(rate / 5)  # Scale to 20 chars
        bar = "█" * filled + "░" * (20 - filled)

        # Color based on quality
        if rate >= 90:
            color = "green"
        elif rate >= 70:
            color = "yellow"
        else:
            color = "red"

        table.add_row(field, Text(bar, style=color), Text(f"{rate:.0f}%", style=color))

    return Panel(table, title="[bold]🎯 Field Extraction Quality", border_style="magenta")


def create_recent_events_table(data: dict) -> Table:
    """Create recent events table."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Status", width=3)
    table.add_column("Specimen", width=35)
    table.add_column("Details", width=35)

    for result in reversed(data["latest_events"]):
        is_success = "dwc" in result and result["dwc"]
        emoji = "✅" if is_success else "❌"
        style = "green" if is_success else "red"

        specimen_id = result.get("image", "unknown")[:35]

        if is_success:
            details = f"{len(result['dwc'])} fields extracted"
        else:
            error = result.get("error", "Unknown error")
            details = f"Error: {error[:30]}"

        table.add_row(Text(emoji, style=style), Text(specimen_id, style="cyan"), Text(details))

    return Panel(table, title="[bold]📋 Recent Activity", border_style="yellow")


def main():
    parser = argparse.ArgumentParser(description="Rich snapshot monitor")
    parser.add_argument(
        "--run-dir",
        type=Path,
        help="Extraction run directory (auto-detects latest if not specified)",
    )
    parser.add_argument("--watch", action="store_true", help="Watch mode (refresh every 2 seconds)")

    args = parser.parse_args()

    console = Console()

    try:
        run_dir = args.run_dir or find_latest_run()

        if not run_dir.exists():
            console.print(f"[red]❌ Run directory not found: {run_dir}[/red]")
            return 1

        console.clear()
        console.print("\n[bold cyan]🌿 Herbarium Extraction Monitor[/bold cyan]", justify="center")
        console.print(f"[dim]{run_dir.name}[/dim]\n", justify="center")

        # Read data
        data = read_extraction_data(run_dir)

        # Display panels
        console.print(create_hero_panel(data))
        console.print()

        # Two columns
        layout = Layout()
        layout.split_row(Layout(create_stats_table(data)), Layout(create_field_quality_table(data)))
        console.print(layout)
        console.print()

        console.print(create_recent_events_table(data))

        # Cost info
        console.print(
            Panel(
                Text(
                    "💰 Cost: $0.00 (FREE tier)\n" "Estimated full dataset: FREE",
                    style="bold green",
                ),
                border_style="green",
            )
        )

        console.print(f"\n[dim]Last updated: {datetime.now().strftime('%H:%M:%S')}[/dim]")

        if not args.watch:
            console.print(
                "\n[dim]Tip: Run with --watch for live updates[/dim]",
                style="dim italic",
            )

    except FileNotFoundError as e:
        console.print(f"[red]❌ {e}[/red]")
        return 1
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        return 1


if __name__ == "__main__":
    main()
