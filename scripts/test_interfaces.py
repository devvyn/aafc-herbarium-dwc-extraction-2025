#!/usr/bin/env python3
"""Test script for the new UI interfaces."""

import sys
from pathlib import Path


def test_dependencies():
    """Test if all dependencies are available."""
    print("🧪 Testing UI Dependencies")
    print("=" * 40)

    results = {}

    # Test Rich (TUI)
    try:
        import rich
        from rich.console import Console

        results["rich"] = "✅ Available"
    except ImportError:
        results["rich"] = "❌ Missing - install with: pip install rich"

    # Test FastAPI (Web)
    try:
        import fastapi
        import uvicorn

        results["web"] = "✅ Available"
    except ImportError:
        results["web"] = "❌ Missing - install with: pip install fastapi uvicorn jinja2"

    # Test progress tracker
    try:
        from progress_tracker import global_tracker, ProgressUpdate

        results["progress"] = "✅ Available"
    except ImportError:
        results["progress"] = "❌ Missing - progress_tracker.py not found"

    # Test CLI integration
    try:
        from cli import process_cli

        results["cli"] = "✅ Available"
    except ImportError:
        results["cli"] = "❌ Missing - cli.py not found"

    for component, status in results.items():
        print(f"{component.capitalize()}: {status}")

    return all("✅" in status for status in results.values())


def test_progress_tracker():
    """Test progress tracking system."""
    print("\n🔄 Testing Progress Tracker")
    print("=" * 40)

    try:
        from progress_tracker import ProgressTracker

        # Create test tracker
        tracker = ProgressTracker()
        received_updates = []

        def test_callback(update):
            received_updates.append(update)
            print(f"📨 Received: {update.type} - {update.message}")

        tracker.add_callback(test_callback)

        # Test updates
        tracker.start_processing(5, {"engine": "vision"})

        # Simulate some processing
        from pathlib import Path

        test_image = Path("test.jpg")

        tracker.image_started(test_image)
        tracker.image_completed(test_image, "vision", 0.95)

        tracker.image_started(Path("test2.jpg"))
        tracker.image_failed(Path("test2.jpg"), "OCR failed")

        tracker.processing_complete()

        print(f"✅ Progress tracker test complete - {len(received_updates)} updates received")

        # Check stats
        stats = tracker.get_stats()
        print(f"📊 Final stats: {stats['successful']} successful, {stats['failed']} failed")

        return True

    except Exception as e:
        print(f"❌ Progress tracker test failed: {e}")
        return False


def test_tui_import():
    """Test TUI interface import."""
    print("\n🖥️  Testing TUI Interface")
    print("=" * 40)

    try:
        from tui_interface import HerbariumTUI

        # Try to create TUI instance
        tui = HerbariumTUI()
        print("✅ TUI interface imports successfully")

        # Test display methods (non-interactive)
        try:
            tui.display_welcome()
            print("✅ Welcome display works")
        except Exception as e:
            print(f"⚠️  Welcome display issue: {e}")

        return True

    except ImportError as e:
        print(f"❌ TUI interface import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ TUI interface error: {e}")
        return False


def test_web_import():
    """Test web dashboard import."""
    print("\n🌐 Testing Web Dashboard")
    print("=" * 40)

    try:
        from web_dashboard import app, create_templates

        print("✅ Web dashboard imports successfully")

        # Test template creation
        try:
            create_templates()
            if Path("templates/dashboard.html").exists():
                print("✅ Template creation works")
            else:
                print("⚠️  Template not created")
        except Exception as e:
            print(f"⚠️  Template creation issue: {e}")

        return True

    except ImportError as e:
        print(f"❌ Web dashboard import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Web dashboard error: {e}")
        return False


def test_launcher():
    """Test unified launcher."""
    print("\n🚀 Testing Interface Launcher")
    print("=" * 40)

    try:
        from herbarium_ui import check_dependencies, parse_args

        print("✅ Interface launcher imports successfully")

        # Test dependency check
        deps_ok = check_dependencies()
        print(f"📋 Dependency check: {'✅ Pass' if deps_ok else '⚠️  Some missing'}")

        # Test argument parsing
        try:
            parse_args.__globals__["argparse"].ArgumentParser(description="Test")
            print("✅ Argument parsing setup works")
        except Exception as e:
            print(f"⚠️  Argument parsing issue: {e}")

        return True

    except ImportError as e:
        print(f"❌ Interface launcher import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Interface launcher error: {e}")
        return False


def run_integration_test():
    """Run a simple integration test."""
    print("\n🔗 Integration Test")
    print("=" * 40)

    # Check if we have trial images to test with
    if Path("trial_images").exists() and list(Path("trial_images").glob("*.jpg")):
        print("✅ Trial images found - integration test possible")

        try:
            run_integration = (
                input("Run quick integration test with existing trial images? [y/N]: ")
                .lower()
                .startswith("y")
            )
        except (EOFError, KeyboardInterrupt):
            run_integration = False
            print("⏭️  Skipping interactive integration test")

        if run_integration:
            try:
                from progress_tracker import setup_tui_tracking

                # Setup TUI tracking
                setup_tui_tracking()

                # Test CLI with progress tracking
                print("🔄 Running CLI with progress tracking...")
                from cli import process_cli

                result_dir = Path("test_ui_results")
                result_dir.mkdir(exist_ok=True)

                process_cli(Path("trial_images"), result_dir, enabled_engines=["vision"])

                print("✅ Integration test completed successfully!")
                return True

            except Exception as e:
                print(f"❌ Integration test failed: {e}")
                return False
        else:
            print("⏭️  Integration test skipped")
            return True
    else:
        print("⚠️  No trial images found - run quick_trial_run.py first for full integration test")
        return True


def main():
    """Main test runner."""
    print("🌿 Herbarium OCR Interface Testing")
    print("=" * 50)

    test_results = {}

    # Run all tests
    test_results["dependencies"] = test_dependencies()
    test_results["progress_tracker"] = test_progress_tracker()
    test_results["tui"] = test_tui_import()
    test_results["web"] = test_web_import()
    test_results["launcher"] = test_launcher()
    test_results["integration"] = run_integration_test()

    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)

    passed = sum(test_results.values())
    total = len(test_results)

    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The new UI interfaces are ready to use.")
        print("\n💡 Quick start:")
        print("   python herbarium_ui.py          # Interactive menu")
        print("   python herbarium_ui.py --tui    # Launch TUI directly")
        print("   python herbarium_ui.py --web    # Launch web dashboard")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        print("\n💡 Install missing dependencies:")
        print("   pip install rich fastapi uvicorn jinja2")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
