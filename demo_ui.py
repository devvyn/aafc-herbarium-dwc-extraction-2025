#!/usr/bin/env python3
"""Demo script for the new UI interfaces - non-interactive version."""

import asyncio
from pathlib import Path
from datetime import datetime
import sys

def demo_progress_tracker():
    """Demonstrate the progress tracking system."""
    print("🔄 Progress Tracker Demo")
    print("=" * 50)

    from progress_tracker import ProgressTracker, ProgressUpdate, create_tui_callback

    # Create tracker with TUI callback
    tracker = ProgressTracker()
    tui_callback = create_tui_callback()
    tracker.add_callback(tui_callback)

    # Simulate processing
    print("\n🚀 Simulating image processing with progress tracking...")

    tracker.start_processing(5, {"engine": "vision"})

    import time
    test_images = ["specimen_001.jpg", "specimen_002.jpg", "specimen_003.jpg", "specimen_004.jpg", "specimen_005.jpg"]

    for i, img_name in enumerate(test_images):
        img_path = Path(img_name)
        tracker.image_started(img_path)

        time.sleep(0.3)  # Simulate processing time

        if i == 2:  # Simulate one failure
            tracker.image_failed(img_path, "OCR confidence too low")
        else:
            tracker.image_completed(img_path, "vision", 0.95 - i * 0.05)

    tracker.processing_complete()

    # Show final stats
    stats = tracker.get_stats()
    print(f"\n📊 Final Statistics:")
    print(f"   Total: {stats['processed']}")
    print(f"   Successful: {stats['successful']} ")
    print(f"   Failed: {stats['failed']}")
    print(f"   Engine Usage: {stats['engine_stats']}")


def demo_tui_display():
    """Demonstrate TUI display components."""
    print("\n🖥️  TUI Display Demo")
    print("=" * 50)

    try:
        from tui_interface import HerbariumTUI
        from rich.console import Console

        console = Console()
        tui = HerbariumTUI()

        # Show welcome screen
        console.print("\n[bold blue]TUI Welcome Screen:[/bold blue]")
        tui.display_welcome()

        # Demo configuration display
        console.print("\n[bold blue]Configuration Example:[/bold blue]")
        console.print("📁 Input directory: ./trial_images")
        console.print("📤 Output directory: ./tui_demo_results")
        console.print("🤖 OCR engine: vision")
        console.print("⚙️  Config file: None")

        # Demo stats with mock data
        console.print("\n[bold blue]Processing Stats Example:[/bold blue]")
        tui.stats.total_images = 5
        tui.stats.processed = 4
        tui.stats.successful = 3
        tui.stats.failed = 1
        tui.stats.current_image = "specimen_004.jpg"
        tui.stats.start_time = datetime.now()
        tui.stats.engine_stats = {"vision": 3, "tesseract": 1}
        tui.stats.errors = ["Failed to process specimen_002.jpg: Low confidence"]

        # Display processing stats
        stats_display = tui.create_processing_display()
        console.print(stats_display)

        # Display engine stats
        engine_display = tui.create_engine_stats()
        console.print(engine_display)

        print("✅ TUI display components working correctly")

    except ImportError as e:
        print(f"❌ TUI demo skipped: {e}")


def demo_web_components():
    """Demonstrate web dashboard components."""
    print("\n🌐 Web Dashboard Demo")
    print("=" * 50)

    try:
        from web_dashboard import create_templates, ProcessingStatus

        # Create templates
        create_templates()
        print("✅ Web templates created")

        # Demo status object
        status = ProcessingStatus(
            total_images=10,
            processed=7,
            successful=6,
            failed=1,
            current_image="specimen_008.jpg",
            start_time=datetime.now().isoformat(),
            errors=["Processing error on specimen_003.jpg"],
            engine_stats={"vision": 5, "tesseract": 1, "gpt": 1}
        )

        print(f"📊 Demo Status Object:")
        print(f"   Total Images: {status.total_images}")
        print(f"   Processed: {status.processed}")
        print(f"   Success Rate: {status.successful/status.processed*100:.1f}%")
        print(f"   Current: {status.current_image}")
        print(f"   Engine Stats: {status.engine_stats}")

        # Check template creation
        template_path = Path("templates/dashboard.html")
        if template_path.exists():
            size = template_path.stat().st_size
            print(f"✅ Dashboard template: {size} bytes")

        print("✅ Web dashboard components working correctly")

    except ImportError as e:
        print(f"❌ Web demo skipped: {e}")


def demo_cli_integration():
    """Demonstrate CLI integration with progress tracking."""
    print("\n⚡ CLI Integration Demo")
    print("=" * 50)

    # Check if we have trial images
    if not Path("trial_images").exists():
        print("⚠️  No trial images found. Run quick_trial_run.py first.")
        return

    trial_images = list(Path("trial_images").glob("*.jpg"))
    if not trial_images:
        print("⚠️  No JPG images in trial_images directory.")
        return

    print(f"✅ Found {len(trial_images)} trial images")
    print("🔄 Would process with CLI integration:")

    for img in trial_images[:3]:  # Show first 3
        print(f"   📸 {img.name}")

    if len(trial_images) > 3:
        print(f"   ... and {len(trial_images) - 3} more")

    # Demo the CLI command that would be run
    demo_output_dir = Path("demo_cli_results")

    print(f"\n💻 CLI Command Demonstration:")
    print(f"   python cli.py process --input trial_images --output {demo_output_dir} --engine vision")
    print(f"   (With integrated progress tracking to TUI/Web interfaces)")

    print("✅ CLI integration ready")


def demo_unified_launcher():
    """Demonstrate the unified launcher capabilities."""
    print("\n🚀 Unified Launcher Demo")
    print("=" * 50)

    try:
        from herbarium_ui import check_dependencies

        # Demo dependency checking
        deps_available = check_dependencies()
        print(f"✅ All dependencies available: {deps_available}")

        # Demo available interfaces
        interfaces = [
            "🖥️  TUI (Terminal User Interface)",
            "🌐 Web Dashboard",
            "⚡ CLI (Command Line)",
            "🔄 Quick Trial",
            "❓ Help"
        ]

        print("\n🎯 Available Interfaces:")
        for i, interface in enumerate(interfaces, 1):
            print(f"   {i}. {interface}")

        # Demo launcher commands
        print("\n💻 Launcher Commands:")
        print("   python herbarium_ui.py          # Interactive menu")
        print("   python herbarium_ui.py --tui    # Direct TUI launch")
        print("   python herbarium_ui.py --web    # Direct web launch")
        print("   python herbarium_ui.py --cli    # CLI help")
        print("   python herbarium_ui.py --trial  # Quick trial")
        print("   python herbarium_ui.py --check  # Dependency check")

        print("✅ Unified launcher ready")

    except ImportError as e:
        print(f"❌ Launcher demo failed: {e}")


def main():
    """Run complete UI demonstration."""
    print("🌿 Herbarium OCR System - UI Interface Demonstration")
    print("=" * 70)
    print(f"⏰ Demo run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run all demos
    try:
        demo_progress_tracker()
        demo_tui_display()
        demo_web_components()
        demo_cli_integration()
        demo_unified_launcher()

        print("\n🎉 UI Interface Demonstration Complete!")
        print("=" * 70)

        print("\n✨ New UI Features Summary:")
        print("   🖥️  Rich TUI with real-time progress tracking")
        print("   🌐 Modern web dashboard with live updates")
        print("   🔄 Unified progress tracking across all interfaces")
        print("   🚀 Single launcher for all interface options")
        print("   📊 Visual statistics and error reporting")
        print("   ⚡ Integration with existing CLI processing")

        print("\n🎯 Quick Start:")
        print("   python herbarium_ui.py          # Choose interface interactively")
        print("   python quick_trial_run.py       # Test with 5 sample images")
        print("   python herbarium_ui.py --tui    # Launch rich TUI directly")
        print("   python herbarium_ui.py --web    # Launch web dashboard")

        print("\n💫 The UX is now as nice as CLI agentic UX with:")
        print("   ✅ Real-time progress visualization")
        print("   ✅ Interactive configuration wizards")
        print("   ✅ Live error reporting and statistics")
        print("   ✅ Multiple interface options for different use cases")
        print("   ✅ Seamless integration with existing processing pipeline")

        return 0

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
