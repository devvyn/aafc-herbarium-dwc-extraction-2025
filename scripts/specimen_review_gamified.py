#!/usr/bin/env python3
"""
Gamified Specimen Review TUI - Weekend Experiment

Prototype for "vertical growth toward perfection" metaphor:
- Dataset quality grows upward (collective progress)
- Personal mastery tracked (learning progress)
- Fun visual feedback (growth stages 🌰 → 🌱 → 🌿 → 🌳 → ✨ → ⭐)

This is a weekend experiment - won't block production work!
"""

import sys
from datetime import datetime
from typing import List, Optional

import requests


class SessionStats:
    """Track gamification stats for current review session."""

    def __init__(self):
        self.session_start = datetime.now()
        self.reviews_today = 0
        self.approvals = 0
        self.rejections = 0
        self.flags = 0
        self.points = 0
        self.families_seen = set()

    def record_review(self, action: str, specimen_data: dict):
        """Record a review action and calculate points."""
        self.reviews_today += 1

        # Track taxonomic families for learning progress
        extracted = specimen_data.get("extracted_data", {})
        if isinstance(extracted, dict):
            family = extracted.get("family", "Unknown")
            if family and family != "Unknown":
                self.families_seen.add(family)

        # Points system (from gamification design)
        points_earned = 0
        if action == "approve":
            self.approvals += 1
            points_earned = 10
        elif action == "reject":
            self.rejections += 1
            points_earned = 15  # Requires thought!
        elif action == "flag":
            self.flags += 1
            points_earned = 20  # Requires judgment!

        # Priority multiplier (with safe access)
        priority = specimen_data.get("priority", "MEDIUM")
        if priority == "CRITICAL":
            points_earned *= 2

        self.points += points_earned
        return points_earned

    def get_growth_stage(self, dataset_quality: float) -> tuple[str, str, str]:
        """Get growth stage emoji, name, and description based on quality."""
        if dataset_quality >= 0.95:
            return "⭐", "Perfect Dataset", "You're approaching perfection!"
        elif dataset_quality >= 0.85:
            return "✨", "High Quality", "Blossoming toward excellence"
        elif dataset_quality >= 0.70:
            return "🌳", "Good Progress", "Growing strong!"
        elif dataset_quality >= 0.50:
            return "🌿", "Growing", "Making steady progress"
        elif dataset_quality >= 0.25:
            return "🌱", "Taking Root", "Getting established"
        else:
            return "🌰", "Seedling", "Just beginning to grow"


class GamifiedReviewTUI:
    """Terminal UI for gamified specimen review."""

    def __init__(self, api_base: str = "http://127.0.0.1:5002"):
        self.api_base = api_base
        self.stats = SessionStats()
        self.queue: List[dict] = []
        self.current_index = 0

    def fetch_queue(self):
        """Fetch review queue from API v2."""
        try:
            response = requests.get(f"{self.api_base}/api/queue?v=2&limit=100")
            response.raise_for_status()
            data = response.json()
            self.queue = data.get("queue", [])
            print(f"✅ Loaded {len(self.queue)} specimens for review")
        except Exception as e:
            print(f"❌ Failed to fetch queue: {e}")
            sys.exit(1)

    def get_current_specimen(self) -> Optional[dict]:
        """Get current specimen details from API."""
        if not self.queue or self.current_index >= len(self.queue):
            return None

        specimen_id = self.queue[self.current_index]["specimen_id"]
        try:
            response = requests.get(f"{self.api_base}/api/specimen/{specimen_id}?v=2")
            response.raise_for_status()
            return response.json()["specimen"]
        except Exception as e:
            print(f"❌ Failed to fetch specimen: {e}")
            return None

    def calculate_dataset_quality(self) -> float:
        """Calculate current dataset quality percentage."""
        # Simple approximation: average quality scores from queue
        if not self.queue:
            return 0.0

        total_quality = sum(s.get("quality_score", 0) for s in self.queue)
        avg_quality = total_quality / len(self.queue) / 100  # Convert to 0-1
        return avg_quality

    def render_vertical_growth_meter(self, quality: float):
        """Render vertical growth meter (core metaphor!)."""
        print()
        print("┌─── VERTICAL GROWTH: DATASET QUALITY ────────────────┐")
        print("│                                                      │")

        milestones = [
            (0.95, "⭐ Perfect Dataset (goal)"),
            (0.85, "✨ High Quality"),
            (0.70, "📈 Good Progress"),
            (0.50, "🌿 Growing Strong"),
            (0.25, "🌱 Taking Root"),
            (0.00, "🌰 Seedling"),
        ]

        for threshold, label in milestones:
            if abs(quality - threshold) < 0.02:
                marker = "┤═══════ 🎯 YOU ARE HERE"
            elif quality > threshold:
                marker = "┤ ✓"
            else:
                marker = "┤"

            print(f"│ {int(threshold * 100):3d}% {marker:40s} │")
            if threshold > 0:
                print(f"│       {label:40s}   │")

        print("│                                                      │")
        print(f"│ Current Quality: {quality * 100:.1f}%                       │")
        print(f"│ Reviews Completed: {self.stats.reviews_today:3d}                           │")
        print("└──────────────────────────────────────────────────────┘")
        print()

    def render_session_stats(self):
        """Render session statistics."""
        print("┌─── TODAY'S SESSION ──────────────────────────────────┐")
        print(
            f"│ Reviews:   {self.stats.reviews_today:3d} specimens                               │"
        )
        print(
            f"│ Approved:  {self.stats.approvals:3d}  |  Rejected: {self.stats.rejections:3d}  |  Flagged: {self.stats.flags:3d}  │"
        )
        print(f"│ Points:    {self.stats.points:4d} pts                                  │")
        print(f"│ Families:  {len(self.stats.families_seen)} unique taxonomic families seen      │")
        print("└──────────────────────────────────────────────────────┘")
        print()

    def render_specimen(self, specimen: dict):
        """Render current specimen for review."""
        print("═" * 60)
        print(f"SPECIMEN #{self.current_index + 1}/{len(self.queue)}")
        print("═" * 60)
        print()

        # Basic specimen info
        print(f"📋 ID: {specimen.get('specimen_id', 'Unknown')}")

        # Priority from queue data (fallback if not in specimen)
        priority = specimen.get("priority")
        if not priority and self.current_index < len(self.queue):
            priority = self.queue[self.current_index].get("priority", "UNKNOWN")
        print(f"🎯 Priority: {priority}")

        # Quality score
        quality_score = specimen.get("quality_score", 0)
        print(f"📊 Quality: {quality_score:.1f}%")

        # Quality indicator (from accessibility metadata)
        if "accessibility" in specimen:
            qi = specimen["accessibility"].get("quality_indicator", {})
            visual = qi.get("visual", {})
            if visual:
                print(f"\n{visual.get('icon', '❓')} {visual.get('text', 'Unknown')}")

        # Extracted data preview
        extracted_data = specimen.get("extracted_data", {})
        if extracted_data:
            print(f"\n🔬 Scientific Name: {extracted_data.get('scientificName', 'N/A')}")
            print(f"🏛️ Family: {extracted_data.get('family', 'N/A')}")
            print(f"📍 Location: {extracted_data.get('locality', 'N/A')}")
            print(f"📅 Date: {extracted_data.get('eventDate', 'N/A')}")

        print()

    def render_controls(self):
        """Render keyboard controls."""
        print("⌨️  [a] Approve  [r] Reject  [f] Flag  [n] Next  [q] Quit")
        print()

    def submit_review(self, specimen_id: str, action: str) -> bool:
        """Submit review action to API."""
        endpoints = {
            "approve": f"/api/specimen/{specimen_id}/approve",
            "reject": f"/api/specimen/{specimen_id}/reject",
            "flag": f"/api/specimen/{specimen_id}/flag",
        }

        if action not in endpoints:
            return False

        try:
            response = requests.post(
                f"{self.api_base}{endpoints[action]}",
                json={"reviewed_by": "gamified_tui_user"},
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"❌ Failed to submit {action}: {e}")
            return False

    def show_achievement(self, points_earned: int, action: str):
        """Show achievement notification."""
        actions_text = {
            "approve": "✅ Approved!",
            "reject": "❌ Rejected",
            "flag": "🚩 Flagged for expert",
        }
        print()
        print("═" * 60)
        print(f"    {actions_text.get(action, action)} +{points_earned} points")
        print("═" * 60)
        print()

    def run(self):
        """Main review loop."""
        print()
        print("=" * 60)
        print("    🌳 GAMIFIED SPECIMEN REVIEW - Weekend Experiment")
        print("=" * 60)
        print()
        print("Welcome! Let's cultivate a perfect dataset together!")
        print()

        self.fetch_queue()

        if not self.queue:
            print("No specimens to review!")
            return

        dataset_quality = self.calculate_dataset_quality()
        emoji, stage, desc = self.stats.get_growth_stage(dataset_quality)
        print(f"🌱 Dataset Status: {emoji} {stage} - {desc}")
        print()

        while self.current_index < len(self.queue):
            # Clear screen (simple version)
            print("\n" * 2)

            # Render growth meter
            dataset_quality = self.calculate_dataset_quality()
            self.render_vertical_growth_meter(dataset_quality)

            # Render stats
            self.render_session_stats()

            # Get and render specimen
            specimen = self.get_current_specimen()
            if not specimen:
                print("❌ Failed to load specimen")
                break

            self.render_specimen(specimen)
            self.render_controls()

            # Get user action
            action = input("Action: ").strip().lower()

            if action == "q":
                print("\n✅ Session complete! Thanks for cultivating the dataset! 🌳")
                break
            elif action == "n":
                self.current_index += 1
                continue
            elif action in ["a", "r", "f"]:
                action_map = {"a": "approve", "r": "reject", "f": "flag"}
                full_action = action_map[action]

                # Submit review
                if self.submit_review(specimen["specimen_id"], full_action):
                    # Record stats and show achievement
                    points = self.stats.record_review(full_action, specimen)
                    self.show_achievement(points, full_action)

                    # Move to next
                    self.current_index += 1
                    input("Press Enter to continue...")
            else:
                print("❌ Invalid action. Use a/r/f/n/q")
                input("Press Enter to continue...")

        # Final summary
        print()
        print("=" * 60)
        print("    🎉 SESSION COMPLETE!")
        print("=" * 60)
        print()
        print(f"Reviews: {self.stats.reviews_today}")
        print(f"Points Earned: {self.stats.points}")
        print(f"Families Explored: {len(self.stats.families_seen)}")
        print()

        # Show growth achieved
        emoji, stage, desc = self.stats.get_growth_stage(dataset_quality)
        print(f"Dataset Status: {emoji} {stage}")
        print(f"{desc}")
        print()
        print("Keep growing toward perfection! 🌱 → 🌿 → 🌳 → ✨ → ⭐")
        print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Gamified specimen review TUI (weekend experiment)"
    )
    parser.add_argument(
        "--api",
        default="http://127.0.0.1:5002",
        help="Review API base URL",
    )
    args = parser.parse_args()

    tui = GamifiedReviewTUI(api_base=args.api)
    tui.run()
