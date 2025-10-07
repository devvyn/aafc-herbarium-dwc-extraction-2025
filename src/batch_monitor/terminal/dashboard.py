"""
Terminal Dashboard for Batch Monitoring

Live updating TUI using Rich library.
"""

import time
from datetime import datetime
from typing import List

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn
from rich.table import Table

from ..engine import BatchMonitorEngine
from ..models import BatchStatus


class BatchDashboard:
    """Live terminal dashboard for monitoring multiple batches."""

    def __init__(self, engine: BatchMonitorEngine):
        """
        Initialize dashboard.

        Args:
            engine: BatchMonitorEngine instance
        """
        self.engine = engine
        self.console = Console()

    def create_batch_panel(self, status: BatchStatus) -> Panel:
        """Create a panel displaying batch status."""
        # Create progress bar
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )

        task_id = progress.add_task(
            f"{status.status_emoji} {status.batch_id[:16]}...",
            total=status.progress.total or 100,
            completed=status.progress.completed,
        )

        # Create info table
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan", justify="right")
        table.add_column(style="white")

        table.add_row("Status:", f"[bold]{status.status}[/bold]")
        table.add_row("Progress:", f"{status.progress.completed}/{status.progress.total}")
        if status.progress.failed > 0:
            table.add_row("Failed:", f"[red]{status.progress.failed}[/red]")

        # Timing info
        table.add_row(
            "Elapsed:", f"{status.timing.elapsed_minutes:.1f} min"
        )

        if status.completion_eta_seconds and status.completion_eta_seconds > 0:
            eta_min = status.completion_eta_seconds / 60
            table.add_row("ETA:", f"~{eta_min:.1f} min")

        if status.is_complete:
            if status.output_file_id:
                table.add_row("Output:", status.output_file_id[:20] + "...")

        # Combine into panel
        from rich.console import Group

        content = Group(progress, "", table)

        title = f"Batch Monitor - {datetime.now().strftime('%H:%M:%S')}"
        return Panel(content, title=title, border_style="blue")

    def create_multi_batch_layout(self, statuses: List[BatchStatus]) -> Layout:
        """Create layout for multiple batches."""
        layout = Layout()

        if len(statuses) == 1:
            layout.update(self.create_batch_panel(statuses[0]))
        else:
            # Split into rows
            layout.split_column(*[Layout() for _ in statuses])
            for i, status in enumerate(statuses):
                layout.children[i].update(self.create_batch_panel(status))

        return layout

    def monitor(
        self, batch_ids: List[str], refresh_interval: int = 30, auto_exit: bool = True
    ):
        """
        Monitor batch jobs with live updating display.

        Args:
            batch_ids: List of batch IDs to monitor
            refresh_interval: Seconds between updates
            auto_exit: Exit when all batches complete
        """
        with Live(
            self.create_multi_batch_layout([]),
            console=self.console,
            refresh_per_second=1,
        ) as live:
            while True:
                # Fetch statuses
                statuses = self.engine.fetch_multiple(batch_ids)

                # Update display
                layout = self.create_multi_batch_layout(statuses)
                live.update(layout)

                # Check if all complete
                if auto_exit and all(s.is_complete for s in statuses):
                    self.console.print("\n[bold green]✅ All batches complete![/bold green]")
                    break

                # Wait before next update
                time.sleep(refresh_interval)

    def monitor_auto(self, refresh_interval: int = 30):
        """
        Auto-discover and monitor all active batches.

        Args:
            refresh_interval: Seconds between updates
        """
        batch_ids = self.engine.get_active_batches()

        if not batch_ids:
            self.console.print("[yellow]No active batches found[/yellow]")
            return

        self.console.print(f"[cyan]Monitoring {len(batch_ids)} active batches...[/cyan]\n")
        self.monitor(batch_ids, refresh_interval)
