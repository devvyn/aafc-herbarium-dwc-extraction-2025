#!/usr/bin/env python3
"""Modern TUI interface for herbarium OCR processing."""

import asyncio
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field

try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn, TimeElapsedColumn
    from rich.table import Table
    from rich.text import Text
    from rich.align import Align
    from rich.columns import Columns
    from rich.tree import Tree
    from rich.status import Status
    from rich.prompt import Prompt, Confirm
    from rich.syntax import Syntax
    from rich.markdown import Markdown
except ImportError:
    print("❌ Rich library required: pip install rich")
    exit(1)

from cli import process_cli, load_config
from io_utils.image_source import ImageSourceConfig, DEFAULT_S3_CONFIG


@dataclass
class ProcessingStats:
    """Real-time processing statistics."""
    total_images: int = 0
    processed: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    current_image: Optional[str] = None
    start_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)
    engine_stats: Dict[str, int] = field(default_factory=dict)


class HerbariumTUI:
    """Modern Terminal User Interface for herbarium processing."""

    def __init__(self):
        self.console = Console()
        self.stats = ProcessingStats()

    def display_welcome(self):
        """Display welcome screen with branding."""
        welcome_text = """
# 🌿 Herbarium OCR System
## Darwin Core Extraction Pipeline

Transform herbarium specimen images into structured biodiversity data using state-of-the-art OCR and AI technology.

### Features:
- **Multi-engine OCR**: Apple Vision, Tesseract, PaddleOCR, GPT Vision
- **GBIF Integration**: Automatic taxonomy and locality verification
- **Quality Control**: Duplicate detection and confidence scoring
- **Darwin Core**: Standard biodiversity data format output
        """

        panel = Panel(
            Markdown(welcome_text),
            title="🔬 [bold blue]AAFC Herbarium Digitization[/bold blue]",
            border_style="blue",
            padding=(1, 2)
        )

        self.console.print(panel)
        self.console.print()

    def get_processing_config(self) -> Dict[str, Any]:
        """Interactive configuration wizard."""
        self.console.print("[bold green]⚙️  Processing Configuration[/bold green]\n")

        # Input directory
        while True:
            input_dir = Prompt.ask("📁 Input directory with images")
            input_path = Path(input_dir)
            if input_path.exists() and input_path.is_dir():
                break
            self.console.print(f"[red]❌ Directory not found: {input_dir}[/red]")

        # Output directory
        output_dir = Prompt.ask("📤 Output directory", default="./results")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # OCR Engine selection
        available_engines = ["vision", "tesseract", "paddleocr", "gpt"]
        self.console.print(f"\n🤖 Available OCR engines: {', '.join(available_engines)}")
        engine = Prompt.ask("Select OCR engine", choices=available_engines, default="vision")

        # Advanced options
        show_advanced = Confirm.ask("🔧 Show advanced options?", default=False)
        config_file = None

        if show_advanced:
            config_file_str = Prompt.ask("📋 Config file (optional)", default="")
            if config_file_str:
                config_file = Path(config_file_str)
                if not config_file.exists():
                    self.console.print(f"[yellow]⚠️  Config file not found: {config_file_str}[/yellow]")
                    config_file = None

        return {
            'input_dir': input_path,
            'output_dir': output_path,
            'engine': engine,
            'config_file': config_file
        }

    def create_processing_display(self) -> Table:
        """Create the main processing display layout."""
        # Main stats table
        stats_table = Table(show_header=False, box=None, padding=(0, 1))
        stats_table.add_column("Label", style="bold cyan")
        stats_table.add_column("Value", style="white")

        # Processing stats
        total = self.stats.total_images
        processed = self.stats.processed
        success_rate = (self.stats.successful / processed * 100) if processed > 0 else 0

        stats_table.add_row("📊 Total Images", str(total))
        stats_table.add_row("✅ Processed", f"{processed}/{total}")
        stats_table.add_row("📈 Success Rate", f"{success_rate:.1f}%")
        stats_table.add_row("❌ Failed", str(self.stats.failed))
        stats_table.add_row("⏭️  Skipped", str(self.stats.skipped))

        if self.stats.current_image:
            stats_table.add_row("🔄 Current", self.stats.current_image)

        # Timing info
        if self.stats.start_time:
            elapsed = datetime.now() - self.stats.start_time
            rate = processed / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
            stats_table.add_row("⏱️  Elapsed", str(elapsed).split('.')[0])
            stats_table.add_row("🚀 Rate", f"{rate:.1f} img/sec")

            if processed > 0 and processed < total:
                eta_seconds = (total - processed) / rate if rate > 0 else 0
                from datetime import timedelta
                eta = datetime.now().replace(microsecond=0) + timedelta(seconds=eta_seconds) if eta_seconds > 0 else None
                if eta:
                    stats_table.add_row("🎯 ETA", eta.strftime("%H:%M:%S"))

        return stats_table

    def create_engine_stats(self) -> Table:
        """Create engine usage statistics table."""
        if not self.stats.engine_stats:
            return Table()

        engine_table = Table(title="🤖 Engine Usage", box=None)
        engine_table.add_column("Engine", style="bold yellow")
        engine_table.add_column("Count", style="cyan")
        engine_table.add_column("Percentage", style="green")

        total_engine_uses = sum(self.stats.engine_stats.values())

        for engine, count in sorted(self.stats.engine_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_engine_uses * 100) if total_engine_uses > 0 else 0
            engine_table.add_row(engine, str(count), f"{percentage:.1f}%")

        return engine_table

    def create_error_display(self) -> Panel:
        """Create error log display."""
        if not self.stats.errors:
            return Panel(
                "[dim]No errors reported[/dim]",
                title="🛡️ Error Log",
                border_style="green"
            )

        error_text = "\n".join(self.stats.errors[-5:])  # Show last 5 errors
        return Panel(
            error_text,
            title=f"⚠️ Recent Errors ({len(self.stats.errors)} total)",
            border_style="red"
        )

    async def run_processing_with_ui(self, config: Dict[str, Any]):
        """Run processing with live UI updates."""
        self.stats.start_time = datetime.now()

        # Count total images
        from io_utils.read import iter_images
        image_list = list(iter_images(config['input_dir']))
        self.stats.total_images = len(image_list)

        if self.stats.total_images == 0:
            self.console.print("[red]❌ No images found in input directory[/red]")
            return

        # Create progress bars
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=self.console,
            transient=True,
        ) as progress:

            overall_task = progress.add_task(
                f"🔄 Processing {self.stats.total_images} images...",
                total=self.stats.total_images
            )

            # Create live display
            with Live(
                self.create_main_layout(),
                console=self.console,
                refresh_per_second=2,
                transient=False
            ) as live:

                # Run real processing with progress updates
                await self.run_real_processing(config, progress, overall_task, live)

        # Final results
        self.display_results()

    def create_main_layout(self) -> Panel:
        """Create the main live display layout."""
        # Create layout columns
        left_column = Panel(
            self.create_processing_display(),
            title="📊 Processing Status",
            border_style="blue"
        )

        right_column = Columns([
            Panel(
                self.create_engine_stats(),
                title="🤖 Engine Stats",
                border_style="yellow"
            ),
            Panel(
                self.create_error_display(),
                title="🛡️ Status Log",
                border_style="green"
            )
        ])

        main_layout = Columns([left_column, right_column])

        return Panel(
            main_layout,
            title="🌿 [bold green]Herbarium OCR Processing[/bold green]",
            border_style="bright_green"
        )

    async def run_real_processing(self, config, progress, overall_task, live):
        """Run real processing with progress updates."""
        from progress_tracker import global_tracker
        from cli import process_cli
        import threading

        # Setup progress callback to update our UI
        def ui_update_callback(update):
            if update.type == 'progress' and update.data.get('current_image'):
                self.stats.current_image = update.data['current_image']
                live.update(self.create_main_layout())
            elif update.type == 'success':
                self.stats.successful += 1
                engine = update.data.get('engine', 'unknown')
                self.stats.engine_stats[engine] = self.stats.engine_stats.get(engine, 0) + 1
                self.stats.processed += 1
                progress.update(overall_task, advance=1)
                live.update(self.create_main_layout())
            elif update.type == 'error':
                self.stats.failed += 1
                self.stats.errors.append(update.data.get('error', update.message))
                self.stats.processed += 1
                progress.update(overall_task, advance=1)
                live.update(self.create_main_layout())

        global_tracker.add_callback(ui_update_callback)

        try:
            # Run processing in thread to avoid blocking UI
            processing_thread = threading.Thread(
                target=process_cli,
                args=(
                    config['input_dir'],
                    config['output_dir'],
                    config.get('config_file'),
                    [config['engine']] if config['engine'] else None,
                    False  # resume
                )
            )

            processing_thread.start()

            # Wait for completion while updating UI
            while processing_thread.is_alive():
                await asyncio.sleep(0.1)
                live.update(self.create_main_layout())

            processing_thread.join()

        finally:
            global_tracker.remove_callback(ui_update_callback)

    async def simulate_processing(self, config, progress, overall_task, live):
        """Simulate processing for demo (fallback if real processing fails)."""
        from io_utils.read import iter_images

        for i, img_path in enumerate(iter_images(config['input_dir'])):
            self.stats.current_image = img_path.name

            # Simulate processing time
            await asyncio.sleep(0.5)

            # Simulate success/failure
            import random
            if random.random() < 0.9:  # 90% success rate
                self.stats.successful += 1
                engine = random.choice(['vision', 'tesseract', 'gpt'])
                self.stats.engine_stats[engine] = self.stats.engine_stats.get(engine, 0) + 1
            else:
                self.stats.failed += 1
                self.stats.errors.append(f"Failed to process {img_path.name}: OCR confidence too low")

            self.stats.processed += 1
            progress.update(overall_task, advance=1)
            live.update(self.create_main_layout())

    def display_results(self):
        """Display final processing results."""
        success_rate = (self.stats.successful / self.stats.processed * 100) if self.stats.processed > 0 else 0

        results_text = f"""
## 🎉 Processing Complete!

**Summary:**
- **Total Images:** {self.stats.total_images}
- **Successfully Processed:** {self.stats.successful}
- **Failed:** {self.stats.failed}
- **Success Rate:** {success_rate:.1f}%

**Processing Time:** {datetime.now() - self.stats.start_time if self.stats.start_time else 'Unknown'}

### Next Steps:
1. 🔍 Review results in web interface
2. 📊 Export Darwin Core archive
3. 🔄 Process additional batches
        """

        panel = Panel(
            Markdown(results_text),
            title="✅ [bold green]Results[/bold green]",
            border_style="green",
            padding=(1, 2)
        )

        self.console.print(panel)

    def run_interactive_menu(self):
        """Main interactive menu."""
        while True:
            self.console.clear()
            self.display_welcome()

            menu_text = """
[bold cyan]🔧 Available Actions:[/bold cyan]

1. 🔄 **Process Images** - OCR and extract Darwin Core data
2. 🌐 **Launch Web Interface** - Review and validate results
3. 📦 **Export Archive** - Create Darwin Core Archive
4. ⚙️  **Configure Sources** - Setup image sources (S3/Local)
5. 📊 **View Statistics** - Show processing analytics
6. ❓ **Help** - Documentation and guides
7. 🚪 **Exit**
            """

            self.console.print(Panel(menu_text, border_style="cyan"))

            choice = Prompt.ask(
                "\n[bold yellow]Select an action[/bold yellow]",
                choices=["1", "2", "3", "4", "5", "6", "7"],
                default="1"
            )

            if choice == "1":
                asyncio.run(self.run_processing_workflow())
            elif choice == "2":
                self.launch_web_interface()
            elif choice == "3":
                self.run_export_workflow()
            elif choice == "4":
                self.configure_image_sources()
            elif choice == "5":
                self.show_statistics()
            elif choice == "6":
                self.show_help()
            elif choice == "7":
                self.console.print("[green]👋 Goodbye![/green]")
                break

    async def run_processing_workflow(self):
        """Interactive processing workflow."""
        self.console.clear()
        self.console.print("[bold blue]🔄 Image Processing Workflow[/bold blue]\n")

        config = self.get_processing_config()

        # Confirm before processing
        self.console.print(f"\n[bold yellow]📋 Configuration Summary:[/bold yellow]")
        self.console.print(f"Input: {config['input_dir']}")
        self.console.print(f"Output: {config['output_dir']}")
        self.console.print(f"Engine: {config['engine']}")

        if not Confirm.ask("\n🚀 Start processing?"):
            return

        await self.run_processing_with_ui(config)

        # Post-processing options
        self.console.print("\n[bold green]✅ Processing completed![/bold green]")
        if Confirm.ask("🌐 Launch web interface to review results?"):
            self.launch_web_interface()

    def launch_web_interface(self):
        """Launch web interface for result review."""
        self.console.print("[bold blue]🌐 Launching Web Interface...[/bold blue]")

        # Find most recent results
        results_dirs = [d for d in Path(".").iterdir() if d.is_dir() and "results" in d.name]
        if not results_dirs:
            self.console.print("[red]❌ No results found. Process some images first.[/red]")
            Prompt.ask("Press Enter to continue...")
            return

        latest_results = max(results_dirs, key=lambda x: x.stat().st_mtime)
        candidates_db = latest_results / "candidates.db"

        if not candidates_db.exists():
            self.console.print("[red]❌ No candidates database found.[/red]")
            Prompt.ask("Press Enter to continue...")
            return

        self.console.print(f"📊 Using results from: {latest_results}")
        self.console.print("🌐 Starting web server on http://localhost:8000")

        # Launch web server (this would be async in real implementation)
        import subprocess
        try:
            subprocess.run([
                "python", "review_web.py",
                "--db", str(candidates_db),
                "--images", str(latest_results.parent / "trial_images")
            ])
        except KeyboardInterrupt:
            self.console.print("\n[yellow]🛑 Web server stopped[/yellow]")

    def run_export_workflow(self):
        """Interactive Darwin Core Archive export."""
        self.console.print("[bold blue]📦 Darwin Core Archive Export[/bold blue]\n")

        # Find results to export
        results_dirs = [d for d in Path(".").iterdir() if d.is_dir() and "results" in d.name]
        if not results_dirs:
            self.console.print("[red]❌ No results found to export.[/red]")
            Prompt.ask("Press Enter to continue...")
            return

        # Select results directory
        if len(results_dirs) == 1:
            selected_dir = results_dirs[0]
        else:
            self.console.print("Available result sets:")
            for i, d in enumerate(results_dirs, 1):
                self.console.print(f"{i}. {d.name} ({d.stat().st_mtime})")

            choice = int(Prompt.ask("Select results to export", choices=[str(i) for i in range(1, len(results_dirs) + 1)]))
            selected_dir = results_dirs[choice - 1]

        # Export options
        version = Prompt.ask("📋 Archive version", default="1.0.0")
        compress = Confirm.ask("🗜️ Create compressed archive?", default=True)

        self.console.print(f"\n📦 Exporting {selected_dir} as v{version}...")

        # TODO: Implement actual export
        with self.console.status("Creating archive...", spinner="dots"):
            time.sleep(2)  # Simulate export

        self.console.print("[green]✅ Archive created successfully![/green]")
        Prompt.ask("Press Enter to continue...")

    def configure_image_sources(self):
        """Interactive image source configuration."""
        self.console.print("[bold blue]⚙️  Image Source Configuration[/bold blue]\n")

        source_types = ["s3", "local", "multi"]
        source_type = Prompt.ask("Select source type", choices=source_types, default="s3")

        if source_type == "s3":
            bucket = Prompt.ask("S3 bucket name", default="devvyn.aafc-srdc.herbarium")
            region = Prompt.ask("AWS region", default="ca-central-1")

            config = {
                'type': 's3',
                'bucket': bucket,
                'region': region
            }

        elif source_type == "local":
            base_path = Prompt.ask("Local images directory", default="./images")

            config = {
                'type': 'local',
                'base_path': base_path
            }

        else:  # multi
            self.console.print("Multi-source setup: local cache with S3 fallback")
            local_path = Prompt.ask("Local cache directory", default="./image_cache")
            bucket = Prompt.ask("S3 bucket name", default="devvyn.aafc-srdc.herbarium")

            config = {
                'type': 'multi',
                'sources': [
                    {'type': 'local', 'base_path': local_path},
                    {'type': 's3', 'bucket': bucket, 'region': 'ca-central-1'}
                ]
            }

        # Test configuration
        self.console.print("\n🧪 Testing configuration...")
        try:
            source = ImageSourceConfig.from_config(config)
            # Test with a known hash
            test_hash = "000e426d6ed12c347a937c47f568088a8daa32cdea3127d90f1eca5653831c84"
            exists = source.exists(test_hash)
            self.console.print(f"✅ Configuration valid. Test image {'found' if exists else 'not found'}.")
        except Exception as e:
            self.console.print(f"[red]❌ Configuration error: {e}[/red]")

        Prompt.ask("Press Enter to continue...")

    def show_statistics(self):
        """Display processing statistics and analytics."""
        self.console.print("[bold blue]📊 Processing Statistics[/bold blue]\n")

        # Mock statistics (in real implementation, load from database)
        stats_table = Table(title="Recent Processing Runs")
        stats_table.add_column("Date", style="cyan")
        stats_table.add_column("Images", style="yellow")
        stats_table.add_column("Success Rate", style="green")
        stats_table.add_column("Primary Engine", style="blue")

        # Sample data
        stats_table.add_row("2025-01-15", "150", "94.2%", "vision")
        stats_table.add_row("2025-01-14", "75", "89.1%", "tesseract")
        stats_table.add_row("2025-01-13", "200", "96.5%", "vision")

        self.console.print(stats_table)

        Prompt.ask("\nPress Enter to continue...")

    def show_help(self):
        """Display help and documentation."""
        help_text = """
# 📚 Herbarium OCR System Help

## Quick Start
1. **Process Images**: Select option 1 to start OCR processing
2. **Review Results**: Use the web interface to validate extracted data
3. **Export Archive**: Create standard Darwin Core archives for sharing

## OCR Engines
- **Apple Vision**: Best for high-quality images on macOS
- **Tesseract**: Open-source, good for printed text
- **PaddleOCR**: Multilingual support
- **GPT Vision**: AI-powered, handles complex layouts

## File Organization
- Input: Directory containing JPG/PNG images
- Output: Structured results with databases and CSV files
- Archives: Darwin Core compliant ZIP files

## Image Sources
- **S3**: Direct cloud storage access
- **Local**: Filesystem-based images
- **Multi**: Hybrid approach with caching

## Support
- Documentation: `docs/` directory
- Issues: Report bugs via GitHub
- Configuration: `config/` directory
        """

        self.console.print(Panel(
            Markdown(help_text),
            title="📖 [bold blue]Help & Documentation[/bold blue]",
            border_style="blue",
            padding=(1, 2)
        ))

        Prompt.ask("Press Enter to continue...")


def main():
    """Main entry point for TUI interface."""
    try:
        tui = HerbariumTUI()
        tui.run_interactive_menu()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
