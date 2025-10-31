"""
NiceGUI Review Interface for Specimen Data

Simplified Python-based UI for reviewing extracted specimen data.
No JavaScript required - all interaction handled by NiceGUI's reactive framework.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict

from nicegui import ui

from .engine import ReviewEngine, ReviewStatus, ReviewPriority, SpecimenReview
from .validators import GBIFValidator
from spatial.zone_loader import ZoneTemplateCache, get_zones_file_path
from spatial.image_annotator import annotate_specimen_image

logger = logging.getLogger(__name__)


class SpecimenReviewUI:
    """NiceGUI-based review interface."""

    def __init__(
        self,
        extraction_dir: Path,
        enable_gbif: bool = False,
        initial_status: Optional[ReviewStatus] = None,
        initial_priority: Optional[ReviewPriority] = None,
        initial_flagged: bool = False,
    ):
        self.extraction_dir = extraction_dir
        self.cache_dir = Path("/tmp/imgcache")
        self.rotation_file = extraction_dir / "image_rotations.json"
        self.zone_overlay_dir = Path("/tmp/zone_overlays")
        self.zone_overlay_dir.mkdir(parents=True, exist_ok=True)

        # Load existing rotations
        self.image_rotations: Dict[str, int] = {}
        if self.rotation_file.exists():
            with open(self.rotation_file, "r") as f:
                self.image_rotations = json.load(f)
            logger.info(
                f"Loaded {len(self.image_rotations)} image rotations from {self.rotation_file}"
            )

        # Zone visualization
        self.show_zones = False  # Default: zones disabled
        self.zone_cache = ZoneTemplateCache()
        zones_file = get_zones_file_path(extraction_dir)
        logger.info(f"Looking for zone templates at: {zones_file}")
        logger.info(f"Zone file exists: {zones_file.exists()}")
        if zones_file.exists():
            try:
                self.zone_cache.load_from_file(zones_file)
                template_count = len(self.zone_cache)
                logger.info(f"Loaded {template_count} zone templates from {zones_file}")

                # Debug: List first few specimen IDs in cache
                if template_count > 0:
                    logger.info(f"Zone cache has {template_count} templates loaded")
                    # Sample check
                    test_ids = [
                        "000e426d6ed12c347a937c47f568088a8daa32cdea3127d90f1eca5653831c84",
                        "002143863d4b7c14afe8d0ea1dcaf8d0aa83b89ac7aebff7ae4a0a76b17f9f10",
                        "002e8642edeadc93e1ed34dfc14a40dc59502ae6ce9aa7d95bb0c0d57d7e0ff5",
                    ]
                    for test_id in test_ids:
                        has_template = self.zone_cache.has(test_id)
                        logger.info(f"  Template for {test_id[:16]}: {has_template}")
                else:
                    logger.warning("Zone cache is empty after loading!")
            except Exception as e:
                logger.warning(f"Failed to load zone templates: {e}", exc_info=True)

        # Initialize review engine
        gbif_validator = GBIFValidator() if enable_gbif else None
        self.engine = ReviewEngine(gbif_validator=gbif_validator)

        # Load extraction results
        results_file = extraction_dir / "raw.jsonl"
        if results_file.exists():
            self.engine.load_extraction_results(results_file)
            logger.info(f"Loaded {len(self.engine.reviews)} specimens for review")
        else:
            logger.error(f"Results file not found: {results_file}")

        # UI state
        self.current_queue: List[SpecimenReview] = []
        self.current_index: int = -1
        self.current_review: Optional[SpecimenReview] = None

        # Filter state - use provided initial values
        self.filter_status: Optional[ReviewStatus] = initial_status
        self.filter_priority: Optional[ReviewPriority] = initial_priority
        self.filter_flagged: bool = initial_flagged

        # Initialize queue data with filters
        self.current_queue = self.engine.get_review_queue(
            status=self.filter_status,
            priority=self.filter_priority,
            flagged_only=self.filter_flagged,
            sort_by="priority",
        )
        self.current_index = 0 if self.current_queue else -1

        # UI components (to be created)
        self.image_widget = None
        self.data_container = None
        self.queue_list = None
        self.stats_label = None
        self.nav_buttons = {}
        self.status_select = None
        self.priority_select = None
        self.flagged_checkbox = None

    def get_image_path(self, specimen_id: str) -> Optional[Path]:
        """Get local cache path for specimen image."""
        sha256 = specimen_id.replace(".jpg", "").replace(".JPG", "")
        if len(sha256) < 4:
            return None

        prefix1 = sha256[:2]
        prefix2 = sha256[2:4]
        image_path = self.cache_dir / prefix1 / prefix2 / f"{sha256}.jpg"

        return image_path if image_path.exists() else None

    def get_image_rotation(self, specimen_id: str) -> int:
        """Get rotation angle for specimen image (0, 90, 180, or 270 degrees)."""
        return self.image_rotations.get(specimen_id, 0)

    def get_annotated_image_path(self, specimen_id: str, rotation: int = 0) -> Optional[Path]:
        """Get or generate annotated image with zone overlays.

        Parameters
        ----------
        specimen_id : str
            Specimen identifier
        rotation : int
            Rotation angle (0, 90, 180, 270)

        Returns
        -------
        Path or None
            Path to annotated image, None if zones not available
        """
        logger.info("get_annotated_image_path called")
        logger.info(f"  FULL specimen_id: {specimen_id}")
        logger.info(f"  specimen_id length: {len(specimen_id)}")
        logger.info(f"  specimen_id type: {type(specimen_id)}")
        logger.info(f"  rotation: {rotation}")
        logger.info(f"  Zone cache size: {len(self.zone_cache)}")
        logger.info(f"  Zone cache type: {type(self.zone_cache)}")

        # Check if zone template exists
        zone_template = self.zone_cache.get(specimen_id)
        logger.info(f"  Zone template found: {zone_template is not None}")

        if not zone_template:
            logger.warning("No zone template in cache for specimen")
            # Double-check cache by listing all cached IDs
            logger.warning("  Checking cache contents...")
            if hasattr(self.zone_cache, "_cache"):
                logger.warning(f"  Cache has {len(self.zone_cache._cache)} entries")
                for cached_id in list(self.zone_cache._cache.keys())[:5]:
                    logger.warning(f"    Cached ID: {cached_id}")
                    logger.warning(f"    Match: {cached_id == specimen_id}")
            return None

        # Check for original image
        image_path = self.get_image_path(specimen_id)
        logger.debug(f"  Image path: {image_path}")
        logger.debug(f"  Image exists: {image_path.exists() if image_path else False}")
        if not image_path:
            logger.warning(f"No image found at expected path for {specimen_id[:16]}")
            return None

        # Generate cache key based on specimen_id and rotation
        cache_key = f"{specimen_id}_{rotation}.jpg"
        annotated_path = self.zone_overlay_dir / cache_key
        logger.debug(f"  Annotated path: {annotated_path}")

        # Return cached version if exists
        if annotated_path.exists():
            logger.debug(f"Using cached zone overlay for {specimen_id[:16]}")
            return annotated_path

        # Generate annotated image
        try:
            logger.info(f"Generating zone overlay for {specimen_id[:16]}")
            logger.info(f"  Input: {image_path}")
            logger.info(f"  Output: {annotated_path}")
            logger.info(f"  Template zones: {len(zone_template.zones_by_text)}")

            annotate_specimen_image(
                image_path=image_path,
                zone_template=zone_template,
                output_path=annotated_path,
                draw_grid=True,
                draw_boxes=True,
            )

            if annotated_path.exists():
                logger.info(
                    f"Successfully generated zone overlay for {specimen_id[:16]} ({annotated_path.stat().st_size} bytes)"
                )
                return annotated_path
            else:
                logger.error(f"Annotation completed but file not found: {annotated_path}")
                return None
        except Exception as e:
            logger.error(
                f"Failed to generate zone overlay for {specimen_id[:16]}: {e}", exc_info=True
            )
            return None

    def toggle_zones(self, checked: bool):
        """Toggle zone visualization on/off."""
        self.show_zones = checked
        logger.info(f"Zone visualization {'enabled' if checked else 'disabled'}")
        # Reload current specimen to apply/remove zones
        if self.current_review:
            self.load_specimen(self.current_index)

    def set_image_rotation(self, specimen_id: str, rotation: int):
        """Set rotation angle for specimen image and save to disk."""
        # Normalize rotation to 0, 90, 180, 270
        rotation = rotation % 360

        if rotation == 0:
            # Remove rotation if set to 0 (no rotation)
            self.image_rotations.pop(specimen_id, None)
        else:
            self.image_rotations[specimen_id] = rotation

        # Save to disk
        self.rotation_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.rotation_file, "w") as f:
            json.dump(self.image_rotations, f, indent=2)

        logger.info(f"Set rotation for {specimen_id} to {rotation}°")

    def apply_filters(self):
        """Apply current filters and refresh queue."""
        logger.info(
            f"Applying filters - status={self.filter_status}, priority={self.filter_priority}, flagged={self.filter_flagged}"
        )
        self.current_queue = self.engine.get_review_queue(
            status=self.filter_status,
            priority=self.filter_priority,
            flagged_only=self.filter_flagged,
            sort_by="priority",
        )
        logger.info(f"Queue filtered to {len(self.current_queue)} specimens")

        # Reset to first item if queue changed
        self.current_index = 0 if self.current_queue else -1

        # Update UI (only if UI is built)
        logger.info("Calling update_queue_display()")
        self.update_queue_display()
        if hasattr(self, "stats_label") and self.stats_label:
            self.update_stats()
        if self.current_queue and hasattr(self, "image_widget"):
            self.load_specimen(0)

    def load_specimen(self, index: int):
        """Load specimen at given index."""
        if not self.current_queue or index < 0 or index >= len(self.current_queue):
            return

        self.current_index = index
        review = self.current_queue[index]
        self.current_review = review

        # Determine which image to display
        rotation = self.get_image_rotation(review.specimen_id)

        if self.show_zones:
            # Try to get annotated image
            image_path = self.get_annotated_image_path(review.specimen_id, rotation)
            if not image_path:
                # Fall back to original if annotation fails
                image_path = self.get_image_path(review.specimen_id)
                logger.warning(
                    f"No zone overlay available for {review.specimen_id[:16]}, showing original"
                )
        else:
            # Show original image
            image_path = self.get_image_path(review.specimen_id)

        # Update image widget
        if image_path and self.image_widget:
            self.image_widget.source = str(image_path)
            # Apply CSS rotation only to non-annotated images (annotated already rotated)
            if self.show_zones:
                self.image_widget.style("")  # No rotation needed, baked into annotated image
            else:
                self.image_widget.style(f"transform: rotate({rotation}deg);")
        elif self.image_widget:
            self.image_widget.source = None
            self.image_widget.style("")

        # Update data fields
        self.update_data_display()
        self.update_queue_display()
        self.update_nav_buttons()

    def update_data_display(self):
        """Update data fields display."""
        if not self.current_review or not self.data_container:
            return

        self.data_container.clear()

        with self.data_container:
            # Header
            ui.label(f"Specimen: {self.current_review.specimen_id}").classes("text-lg font-bold")
            ui.label(
                f"Quality: {self.current_review.quality_score:.1f}% | "
                f"Priority: {self.current_review.priority.name} | "
                f"Status: {self.current_review.status.name}"
            ).classes("text-sm text-gray-600")

            ui.separator()

            # Core fields
            ui.label("Core Darwin Core Fields").classes("text-md font-semibold mt-4")
            core_fields = [
                "catalogNumber",
                "scientificName",
                "eventDate",
                "recordedBy",
                "locality",
                "country",
                "stateProvince",
            ]

            for field in core_fields:
                field_data = self.current_review.dwc_fields.get(field, {})
                if isinstance(field_data, dict):
                    value = field_data.get("value", "")
                    confidence = field_data.get("confidence", 0)
                else:
                    value = field_data
                    confidence = 0

                with ui.row().classes("w-full items-center gap-2"):
                    ui.label(f"{field}:").classes("w-32 text-sm text-gray-700")
                    ui.input(value=str(value)).classes("flex-1").props("outlined dense")
                    if confidence > 0:
                        ui.label(f"{confidence * 100:.0f}%").classes("text-xs text-gray-500")

            # Issues
            if self.current_review.critical_issues:
                ui.label("Critical Issues").classes("text-md font-semibold mt-4 text-red-600")
                for issue in self.current_review.critical_issues:
                    ui.label(f"• {issue}").classes("text-sm text-red-600")

            if self.current_review.warnings:
                ui.label("Warnings").classes("text-md font-semibold mt-4 text-yellow-600")
                for warning in self.current_review.warnings:
                    ui.label(f"• {warning}").classes("text-sm text-yellow-600")

    def render_queue_list(self):
        """Render the queue list (called by refreshable decorator)."""
        for idx, review in enumerate(self.current_queue[:100]):  # Show first 100 (scrollable)
            is_active = idx == self.current_index
            bg_class = "bg-blue-100" if is_active else "bg-white hover:bg-gray-50"

            # Use functools.partial to avoid lambda closure issues
            from functools import partial

            with (
                ui.card()
                .classes(f"{bg_class} cursor-pointer mb-2")
                .on("click", partial(self.load_specimen, idx))
            ):
                with ui.row().classes("w-full items-center"):
                    ui.label(review.specimen_id[:40]).classes("text-xs flex-1")
                    ui.badge(review.priority.name).classes("text-xs")
                ui.label(
                    f"Quality: {review.quality_score:.0f}% | Issues: {len(review.critical_issues)}"
                ).classes("text-xs text-gray-600")

    def update_queue_display(self):
        """Update queue list display."""
        logger.info("update_queue_display() called")
        if hasattr(self, "queue_list_refresh"):
            logger.info("Calling queue_list_refresh()")
            self.queue_list_refresh()
            logger.info("queue_list_refresh() completed")
        else:
            logger.warning("queue_list_refresh not available yet!")

    def update_stats(self):
        """Update statistics display."""
        if not self.stats_label:
            return

        stats = self.engine.get_statistics()
        self.stats_label.text = (
            f"Total: {stats['total_specimens']} | "
            f"Pending: {stats['status_counts']['PENDING']} | "
            f"Approved: {stats['status_counts']['APPROVED']} | "
            f"Flagged: {stats['flagged_count']} | "
            f"Filtered: {len(self.current_queue)}"
        )

    def update_nav_buttons(self):
        """Update navigation button states."""
        has_prev = self.current_index > 0
        has_next = self.current_index < len(self.current_queue) - 1
        has_current = self.current_review is not None

        if "prev" in self.nav_buttons:
            self.nav_buttons["prev"].enabled = has_prev
        if "next" in self.nav_buttons:
            self.nav_buttons["next"].enabled = has_next
        if "approve" in self.nav_buttons:
            self.nav_buttons["approve"].enabled = has_current
        if "reject" in self.nav_buttons:
            self.nav_buttons["reject"].enabled = has_current
        if "flag" in self.nav_buttons:
            self.nav_buttons["flag"].enabled = has_current

    def next_specimen(self):
        """Load next specimen."""
        if self.current_index < len(self.current_queue) - 1:
            self.load_specimen(self.current_index + 1)

    def prev_specimen(self):
        """Load previous specimen."""
        if self.current_index > 0:
            self.load_specimen(self.current_index - 1)

    def approve_specimen(self):
        """Approve current specimen."""
        if not self.current_review:
            return

        self.engine.update_review(
            specimen_id=self.current_review.specimen_id,
            status=ReviewStatus.APPROVED,
            reviewed_by="curator",
        )

        ui.notify(f"Approved: {self.current_review.specimen_id[:40]}", type="positive")
        self.next_specimen()

    def reject_specimen(self):
        """Reject current specimen."""
        if not self.current_review:
            return

        self.engine.update_review(
            specimen_id=self.current_review.specimen_id,
            status=ReviewStatus.REJECTED,
            reviewed_by="curator",
        )

        ui.notify(f"Rejected: {self.current_review.specimen_id[:40]}", type="negative")
        self.next_specimen()

    def flag_specimen(self):
        """Flag current specimen."""
        if not self.current_review:
            return

        new_flagged = not self.current_review.flagged
        self.engine.update_review(
            specimen_id=self.current_review.specimen_id, flagged=new_flagged, reviewed_by="curator"
        )

        flag_text = "Flagged" if new_flagged else "Unflagged"
        ui.notify(f"{flag_text}: {self.current_review.specimen_id[:40]}", type="warning")
        self.load_specimen(self.current_index)  # Refresh

    def rotate_image_left(self):
        """Rotate current image 90° counter-clockwise."""
        if not self.current_review:
            return

        current_rotation = self.get_image_rotation(self.current_review.specimen_id)
        new_rotation = (current_rotation - 90) % 360
        self.set_image_rotation(self.current_review.specimen_id, new_rotation)

        ui.notify(f"Rotated image {new_rotation}°", type="info")
        self.load_specimen(self.current_index)  # Refresh to apply rotation

    def rotate_image_right(self):
        """Rotate current image 90° clockwise."""
        if not self.current_review:
            return

        current_rotation = self.get_image_rotation(self.current_review.specimen_id)
        new_rotation = (current_rotation + 90) % 360
        self.set_image_rotation(self.current_review.specimen_id, new_rotation)

        ui.notify(f"Rotated image {new_rotation}°", type="info")
        self.load_specimen(self.current_index)  # Refresh to apply rotation

    def reset_image_rotation(self):
        """Reset image rotation to 0°."""
        if not self.current_review:
            return

        self.set_image_rotation(self.current_review.specimen_id, 0)
        ui.notify("Reset image rotation", type="info")
        self.load_specimen(self.current_index)  # Refresh to apply rotation

    def build_ui(self):
        """Build the NiceGUI interface."""
        ui.page_title("Specimen Review - AAFC Herbarium")

        # Header
        with ui.header().classes("items-center justify-between bg-gray-800 text-white p-4"):
            ui.label("🔬 Specimen Review").classes("text-xl font-bold")
            self.stats_label = ui.label("Loading...").classes("text-sm")

        # Main layout
        with ui.row().classes("w-full h-screen"):
            # Left sidebar - Fixed filters + scrollable queue
            with ui.column().classes("w-80 bg-gray-100 flex flex-col"):
                # Fixed header and filters (don't scroll)
                with ui.column().classes("p-4 flex-shrink-0"):
                    ui.label("Review Queue").classes("text-lg font-bold mb-4")

                    # Filters
                    ui.label("Filters").classes("text-sm font-semibold mt-2")

                    with ui.card().classes("w-full p-2 mb-2"):
                        ui.label("Status").classes("text-xs text-gray-600")
                        self.status_select = ui.select(
                            options={None: "All", **{s: s.name for s in ReviewStatus}},
                            value=self.filter_status,
                            on_change=lambda e: self.set_status_filter(e.value),
                        ).classes("w-full")

                    with ui.card().classes("w-full p-2 mb-2"):
                        ui.label("Priority").classes("text-xs text-gray-600")
                        self.priority_select = ui.select(
                            options={None: "All", **{p: p.name for p in ReviewPriority}},
                            value=self.filter_priority,
                            on_change=lambda e: self.set_priority_filter(e.value),
                        ).classes("w-full")

                    with ui.card().classes("w-full p-2 mb-4"):
                        self.flagged_checkbox = ui.checkbox(
                            "Flagged only",
                            value=self.filter_flagged,
                            on_change=lambda e: self.set_flagged_filter(e.value),
                        )

                    ui.separator()

                # Scrollable queue list (takes remaining space)
                # Create a container for the refreshable content
                with ui.column().classes("flex-1 overflow-y-auto px-4"):

                    @ui.refreshable
                    def queue_list_content():
                        for idx, review in enumerate(self.current_queue[:100]):
                            is_active = idx == self.current_index
                            bg_class = "bg-blue-100" if is_active else "bg-white hover:bg-gray-50"

                            # Use functools.partial to avoid lambda closure issues
                            from functools import partial

                            with (
                                ui.card()
                                .classes(f"{bg_class} cursor-pointer mb-2")
                                .on("click", partial(self.load_specimen, idx))
                            ):
                                with ui.row().classes("w-full items-center"):
                                    ui.label(review.specimen_id[:40]).classes("text-xs flex-1")
                                    ui.badge(review.priority.name).classes("text-xs")
                                ui.label(
                                    f"Quality: {review.quality_score:.0f}% | Issues: {len(review.critical_issues)}"
                                ).classes("text-xs text-gray-600")

                    queue_list_content()
                    self.queue_list_refresh = queue_list_content.refresh

            # Middle - Image (with independent scrolling)
            with ui.column().classes("flex-1 p-4 bg-gray-50"):
                with ui.row().classes("w-full items-center justify-between mb-2"):
                    ui.label("Specimen Image").classes("text-lg font-bold")
                    # Controls
                    with ui.row().classes("gap-2 items-center"):
                        # Zone visualization toggle
                        ui.checkbox(
                            "Show zones",
                            value=self.show_zones,
                            on_change=lambda e: self.toggle_zones(e.value),
                        ).classes("text-xs")
                        ui.separator().props("vertical")
                        # Rotation controls
                        with ui.row().classes("gap-1"):
                            ui.button("↶ Rotate Left", on_click=self.rotate_image_left).props(
                                "dense flat"
                            ).classes("text-xs")
                            ui.button("↷ Rotate Right", on_click=self.rotate_image_right).props(
                                "dense flat"
                            ).classes("text-xs")
                            ui.button("⟲ Reset", on_click=self.reset_image_rotation).props(
                                "dense flat"
                            ).classes("text-xs")

                # Image container with independent overflow - fixed height for true independence
                with ui.scroll_area().classes("w-full").style("height: calc(100vh - 220px)"):
                    self.image_widget = ui.image().classes("w-full")

                # Navigation buttons (fixed at bottom)
                with ui.row().classes("mt-4 gap-2"):
                    self.nav_buttons["prev"] = ui.button(
                        "← Previous", on_click=self.prev_specimen
                    ).props("outline")
                    self.nav_buttons["next"] = ui.button(
                        "Next →", on_click=self.next_specimen
                    ).props("outline")
                    ui.separator().props("vertical")
                    self.nav_buttons["approve"] = ui.button(
                        "✓ Approve", on_click=self.approve_specimen, color="positive"
                    )
                    self.nav_buttons["flag"] = ui.button(
                        "⚠ Flag", on_click=self.flag_specimen, color="warning"
                    )
                    self.nav_buttons["reject"] = ui.button(
                        "✗ Reject", on_click=self.reject_specimen, color="negative"
                    )

            # Right - Data fields
            with ui.column().classes("w-96 p-4 bg-white overflow-y-auto"):
                ui.label("Darwin Core Fields").classes("text-lg font-bold mb-4")
                self.data_container = ui.column().classes("w-full")

        # Keyboard shortcuts
        ui.keyboard(on_key=self.handle_keyboard)

        # Load initial specimen after event loop starts
        def initialize_ui():
            if self.current_queue:
                self.load_specimen(0)
            self.update_stats()

        ui.timer(0.1, initialize_ui, once=True)

    def set_status_filter(self, value):
        """Set status filter."""
        logger.info(f"Status filter changed to: {value}")
        self.filter_status = value
        self.apply_filters()

    def set_priority_filter(self, value):
        """Set priority filter."""
        logger.info(f"Priority filter changed to: {value}")
        self.filter_priority = value
        self.apply_filters()

    def set_flagged_filter(self, checked):
        """Set flagged filter."""
        logger.info(f"Flagged filter changed to: {checked}")
        self.filter_flagged = checked
        self.apply_filters()

    def handle_keyboard(self, event):
        """Handle keyboard shortcuts."""
        key = event.key

        if key == "j":
            self.next_specimen()
        elif key == "k":
            self.prev_specimen()
        elif key == "a":
            self.approve_specimen()
        elif key == "x":
            self.reject_specimen()
        elif key == "f":
            self.flag_specimen()
        elif key == "r":
            self.rotate_image_right()
        elif key == "l":
            self.rotate_image_left()
        elif key == "0":
            self.reset_image_rotation()


def create_nicegui_app(extraction_dir: Path, enable_gbif: bool = False) -> None:
    """Create and run NiceGUI review application."""
    review_ui = SpecimenReviewUI(extraction_dir, enable_gbif)
    review_ui.build_ui()


def main():
    """Launch NiceGUI review application."""
    import argparse

    parser = argparse.ArgumentParser(description="Launch specimen review interface (NiceGUI)")
    parser.add_argument(
        "--extraction-dir",
        type=Path,
        required=True,
        help="Directory containing raw.jsonl",
    )
    parser.add_argument("--port", type=int, default=5002, help="Port to run on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument(
        "--no-gbif",
        action="store_true",
        help="Disable GBIF validation",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("SPECIMEN REVIEW INTERFACE (NiceGUI)")
    print("=" * 70)
    print(f"Extraction directory: {args.extraction_dir}")
    print(f"GBIF validation: {'disabled' if args.no_gbif else 'enabled'}")
    print(f"Server: http://{args.host}:{args.port}")
    print()

    create_nicegui_app(extraction_dir=args.extraction_dir, enable_gbif=not args.no_gbif)

    print("✅ Review system ready")
    print(f"🌐 Open: http://{args.host}:{args.port}")
    print()

    ui.run(host=args.host, port=args.port, title="Specimen Review - AAFC Herbarium", reload=False)


if __name__ == "__main__":
    main()
