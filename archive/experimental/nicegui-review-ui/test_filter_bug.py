#!/usr/bin/env python3
"""
Selenium test to diagnose the filter disappearance bug.
"""

import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuration
URL = "http://127.0.0.1:5003"
SCREENSHOT_DIR = Path("/tmp/nicegui_screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)


def main():
    print("=" * 70)
    print("NICEGUI FILTER BUG DIAGNOSTIC")
    print("=" * 70)

    # Use Safari since that's what user is testing with
    print("\n1. Launching Safari WebDriver...")
    driver = webdriver.Safari()

    try:
        # Load the page
        print(f"2. Loading {URL}...")
        driver.get(URL)

        # Wait for page to load
        print("3. Waiting for page load...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)  # Extra wait for NiceGUI to fully render

        # Take initial screenshot
        screenshot_path = SCREENSHOT_DIR / "01_initial_load.png"
        driver.save_screenshot(str(screenshot_path))
        print(f"   ✓ Screenshot saved: {screenshot_path}")

        # Count queue items initially
        print("\n4. Inspecting initial queue list...")
        try:
            # Look for cards in the queue (they have cursor-pointer class)
            cards = driver.find_elements(By.CSS_SELECTOR, ".cursor-pointer.mb-2")
            print(f"   Found {len(cards)} queue items initially")

            # Print first few specimen IDs
            for i, card in enumerate(cards[:3]):
                try:
                    label = card.find_element(By.TAG_NAME, "span")
                    print(f"   - Item {i + 1}: {label.text[:40]}")
                except Exception:
                    pass
        except Exception as e:
            print(f"   ⚠️  Could not find queue items: {e}")

        # Check browser console logs (Safari doesn't support get_log)
        print("\n5. Skipping console check (Safari WebDriver doesn't support it)...")

        # Now interact with a filter (NiceGUI uses select dropdowns, not radios)
        print("\n6. Clicking Status dropdown to change from PENDING...")
        try:
            # Find the Status dropdown (look for select elements or NiceGUI q-select)
            status_dropdown = driver.find_element(By.CSS_SELECTOR, ".q-select")
            status_dropdown.click()
            print("   ✓ Clicked Status dropdown")
            time.sleep(1)

            # Try to find and click an option (e.g., "All")
            try:
                # NiceGUI renders options in a popup menu
                all_option = driver.find_element(By.XPATH, "//*[contains(text(), 'All')]")
                all_option.click()
                print("   ✓ Selected 'All' option")
                time.sleep(2)  # Wait for refresh
            except Exception as e2:
                print(f"   ⚠️  Could not select option: {e2}")
        except Exception as e:
            print(f"   ✗ Could not find dropdown: {e}")
            # Debug: find what selects exist
            selects = driver.find_elements(By.TAG_NAME, "select")
            q_selects = driver.find_elements(By.CSS_SELECTOR, ".q-select")
            print(f"   Found {len(selects)} <select> elements")
            print(f"   Found {len(q_selects)} .q-select elements")

        # Take screenshot after filter click
        screenshot_path = SCREENSHOT_DIR / "02_after_filter_click.png"
        driver.save_screenshot(str(screenshot_path))
        print(f"   ✓ Screenshot saved: {screenshot_path}")

        # Count queue items after filter
        print("\n7. Inspecting queue list after filter...")
        try:
            cards = driver.find_elements(By.CSS_SELECTOR, ".cursor-pointer.mb-2")
            print(f"   Found {len(cards)} queue items after filter")

            if len(cards) == 0:
                print("   ⚠️  BUG REPRODUCED: Queue list disappeared!")

                # Check if elements exist but are hidden
                all_cards = driver.find_elements(By.TAG_NAME, "div")
                print(f"   Total divs on page: {len(all_cards)}")

                # Check for NiceGUI refresh markers
                refresh_markers = driver.find_elements(
                    By.CSS_SELECTOR, "[data-nicegui-refreshable]"
                )
                print(f"   NiceGUI refreshable elements: {len(refresh_markers)}")
        except Exception as e:
            print(f"   ⚠️  Error inspecting queue: {e}")

        # Skip console check for Safari
        print("\n8. Skipping console check (Safari limitation)...")

        # Get page source for inspection
        print("\n9. Saving page source for inspection...")
        source_path = SCREENSHOT_DIR / "page_source_after_filter.html"
        with open(source_path, "w") as f:
            f.write(driver.page_source)
        print(f"   ✓ Page source saved: {source_path}")

        print("\n" + "=" * 70)
        print("DIAGNOSTIC COMPLETE")
        print("=" * 70)
        print(f"Screenshots and HTML saved to: {SCREENSHOT_DIR}")
        print("\nKeeping browser open for 10 seconds for manual inspection...")
        time.sleep(10)

    finally:
        print("\nClosing browser...")
        driver.quit()


if __name__ == "__main__":
    main()
