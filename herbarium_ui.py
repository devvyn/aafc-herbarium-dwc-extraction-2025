#!/usr/bin/env python3
"""Unified interface launcher for herbarium OCR system."""

import sys
import argparse
from pathlib import Path


def check_dependencies():
    """Check if required UI dependencies are available."""
    import importlib.util

    missing = []

    # Check for TUI dependencies
    if importlib.util.find_spec("rich") is None:
        missing.append("rich (for TUI): pip install rich")

    # Check for web dependencies
    if importlib.util.find_spec("fastapi") is None or importlib.util.find_spec("uvicorn") is None:
        missing.append("fastapi uvicorn (for web): pip install fastapi uvicorn jinja2")

    if missing:
        print("❌ Missing dependencies:")
        for dep in missing:
            print(f"   {dep}")
        print("\nInstall missing dependencies and try again.")
        return False

    return True


def show_interface_menu():
    """Show interface selection menu."""
    menu = """
🌿 Herbarium OCR System - Interface Selection

Choose your preferred interface:

1. 🖥️  **TUI (Terminal User Interface)**
   - Rich, interactive terminal experience
   - Real-time progress tracking
   - Keyboard navigation
   - Best for: Command-line users, server environments

2. 🌐 **Web Dashboard**
   - Modern web interface with real-time updates
   - Visual charts and statistics
   - Multi-user support
   - Best for: Teams, visual monitoring

3. ⚡ **CLI (Command Line)**
   - Traditional command-line interface
   - Scriptable and automatable
   - Minimal resource usage
   - Best for: Batch processing, automation

4. 🔄 **Quick Trial**
   - Fast 5-image demo
   - No configuration needed
   - Good for testing
   - Best for: First-time users, demos

5. ❓ **Help**
   - Documentation and guides
"""

    print(menu)

    while True:
        choice = input("Select interface [1-5]: ").strip()

        if choice == "1":
            launch_tui()
            break
        elif choice == "2":
            launch_web_dashboard()
            break
        elif choice == "3":
            launch_cli()
            break
        elif choice == "4":
            launch_quick_trial()
            break
        elif choice == "5":
            show_help()
        else:
            print("❌ Invalid choice. Please select 1-5.")


def launch_tui():
    """Launch the Terminal User Interface."""
    print("🖥️  Launching Terminal User Interface...")

    try:
        from tui_interface import main as tui_main

        tui_main()
    except ImportError:
        print("❌ TUI dependencies not available. Install with: pip install rich")
    except KeyboardInterrupt:
        print("\n👋 TUI session ended.")


def launch_web_dashboard():
    """Launch the Web Dashboard."""
    print("🌐 Launching Web Dashboard...")
    print("📊 Dashboard will be available at http://localhost:8000")

    try:
        from web_dashboard import main as web_main

        web_main()
    except ImportError:
        print("❌ Web dependencies not available. Install with: pip install fastapi uvicorn jinja2")
    except KeyboardInterrupt:
        print("\n👋 Web dashboard stopped.")


def launch_cli():
    """Launch the traditional CLI interface."""
    print("⚡ Traditional CLI Mode")
    print("Usage examples:")
    print("  python cli.py process --input ./images --output ./results")
    print("  python cli.py resume --input ./images --output ./results")
    print("  python cli.py export --output ./results --version 1.0.0")
    print("\nFor full help: python cli.py --help")

    # Offer to run with example args
    if input("\n🚀 Run with example arguments? [y/N]: ").lower().startswith("y"):
        import subprocess

        # Check if we have trial images
        if Path("trial_images").exists():
            print("🔄 Processing trial images...")
            try:
                subprocess.run(
                    [
                        sys.executable,
                        "cli.py",
                        "process",
                        "--input",
                        "trial_images",
                        "--output",
                        "cli_results",
                        "--engine",
                        "vision",
                    ],
                    check=True,
                )
                print("✅ Processing complete! Results in cli_results/")
            except subprocess.CalledProcessError as e:
                print(f"❌ Processing failed: {e}")
        else:
            print(
                "❌ No trial images found. Run quick trial first or specify your own image directory."
            )


def launch_quick_trial():
    """Launch the quick trial run."""
    print("🔄 Launching Quick Trial (5 images)...")
    print("This will download 5 test images and process them with Apple Vision OCR.")

    if input("Continue? [Y/n]: ").lower().startswith("n"):
        return

    try:
        import subprocess

        result = subprocess.run(
            [sys.executable, "quick_trial_run.py"], capture_output=False, text=True
        )

        if result.returncode == 0:
            print("\n✅ Quick trial completed!")
            if input("🌐 Launch web interface to review results? [Y/n]: ").lower().startswith("y"):
                try:
                    subprocess.run(
                        [
                            sys.executable,
                            "review_web.py",
                            "--db",
                            "trial_results/candidates.db",
                            "--images",
                            "trial_images",
                        ]
                    )
                except KeyboardInterrupt:
                    print("\n👋 Review session ended.")
        else:
            print("❌ Quick trial failed. Check the output above for details.")

    except FileNotFoundError:
        print("❌ quick_trial_run.py not found. Make sure you're in the correct directory.")
    except KeyboardInterrupt:
        print("\n👋 Quick trial cancelled.")


def show_help():
    """Show help and documentation."""
    help_text = """
🌿 Herbarium OCR System Help

## Overview
The Herbarium OCR System transforms specimen images into structured Darwin Core data using multiple OCR engines and AI technology.

## Interface Options

### 🖥️ TUI (Terminal User Interface)
- Interactive terminal experience with Rich library
- Real-time progress bars and status updates
- Menu-driven navigation
- Live statistics and error reporting
- Best for interactive use on command line

### 🌐 Web Dashboard
- Modern web interface with real-time updates
- Visual charts showing processing statistics
- WebSocket-based live updates
- Multi-user support
- Access via browser at http://localhost:8000

### ⚡ CLI (Command Line Interface)
- Traditional command-line tool using Typer
- Fully scriptable and automatable
- Minimal resource usage
- Three main commands:
  - `process`: OCR and extract data from images
  - `resume`: Continue interrupted processing
  - `export`: Create Darwin Core Archive

### 🔄 Quick Trial
- Demonstrates the system with 5 test images
- Downloads from S3 and processes with Apple Vision
- Creates reviewable results in trial_results/
- Perfect for first-time users and demos

## File Structure
- **Input**: Directory containing JPG/PNG specimen images
- **Output**: Structured results including:
  - `app.db`: Main application database
  - `candidates.db`: OCR candidate results
  - `manifest.json`: Run metadata
  - `raw.jsonl`: Raw processing events
  - Darwin Core CSV files

## Configuration
- **Default config**: `config/config.default.toml`
- **User config**: Override with `--config` parameter
- **Image sources**: Configure S3 or local filesystem access
- **OCR engines**: Enable/disable engines per project needs

## OCR Engines
- **Apple Vision**: macOS only, excellent for high-quality images
- **Tesseract**: Cross-platform, good for printed text
- **PaddleOCR**: Multilingual support, good for diverse content
- **GPT Vision**: AI-powered, handles complex layouts

## Quality Control
- **GBIF Integration**: Automatic taxonomy and locality verification
- **Duplicate Detection**: SHA256 and perceptual hash comparison
- **Confidence Scoring**: OCR confidence thresholds
- **Error Tracking**: Comprehensive error logging and retry logic

## Getting Started
1. **First time**: Run Quick Trial to test the system
2. **Regular use**: Choose TUI for interactive sessions
3. **Monitoring**: Use Web Dashboard for team environments
4. **Automation**: Use CLI for scripted workflows

## Support
- **Documentation**: Check docs/ directory
- **Issues**: Report problems via GitHub
- **Configuration**: Examples in config/ directory
- **Testing**: Use test_regression.sh for validation

## Dependencies
- **Core**: Python 3.11+, uv package manager
- **TUI**: rich library (`pip install rich`)
- **Web**: fastapi, uvicorn (`pip install fastapi uvicorn jinja2`)
- **OCR**: Engine-specific requirements (see docs)
"""

    print(help_text)
    input("\nPress Enter to continue...")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="🌿 Herbarium OCR System - Unified Interface Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Interactive menu
  %(prog)s --tui             # Launch TUI directly
  %(prog)s --web             # Launch web dashboard
  %(prog)s --cli             # Show CLI help
  %(prog)s --trial           # Run quick trial
        """,
    )

    parser.add_argument("--tui", action="store_true", help="Launch TUI directly")
    parser.add_argument("--web", action="store_true", help="Launch web dashboard")
    parser.add_argument("--cli", action="store_true", help="Show CLI usage")
    parser.add_argument("--trial", action="store_true", help="Run quick trial")
    parser.add_argument("--check", action="store_true", help="Check dependencies only")

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Check dependencies first
    if not check_dependencies():
        if not args.check:
            print(
                "\n💡 Tip: You can still use the basic CLI interface without additional dependencies."
            )
            if input("Continue with CLI help? [y/N]: ").lower().startswith("y"):
                launch_cli()
        return 1

    if args.check:
        print("✅ All dependencies are available!")
        return 0

    # Direct launches
    if args.tui:
        launch_tui()
    elif args.web:
        launch_web_dashboard()
    elif args.cli:
        launch_cli()
    elif args.trial:
        launch_quick_trial()
    else:
        # Interactive menu
        try:
            show_interface_menu()
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
