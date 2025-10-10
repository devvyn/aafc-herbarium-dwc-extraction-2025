#!/usr/bin/env python
"""
Interactive CLI Correction Tool with GBIF Autocomplete

Fast expert review and correction of extraction results.
Supports keyboard navigation, autocomplete, and image preview.

Usage:
    python scripts/correct_interactive.py \
        --input full_dataset_processing/gpt4omini_batch/raw.jsonl \
        --output full_dataset_processing/gpt4omini_batch/corrected.jsonl \
        --images /tmp/imgcache
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
except ImportError:
    print("Error: rich library not installed")
    print("Install with: uv add rich")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Error: requests library not installed")
    print("Install with: uv add requests")
    sys.exit(1)

try:
    from PIL import Image
    from rich_pixels import Pixels
except ImportError:
    Pixels = None


console = Console()


class GBIFAutocomplete:
    """GBIF Species API autocomplete."""

    BASE_URL = "https://api.gbif.org/v1/species"

    @classmethod
    def suggest_scientific_name(cls, query: str, limit: int = 10) -> List[Dict]:
        """Get scientific name suggestions from GBIF.

        Args:
            query: Partial scientific name
            limit: Maximum suggestions to return

        Returns:
            List of matches with name, authority, and key
        """
        if not query or len(query) < 2:
            return []

        try:
            response = requests.get(
                f"{cls.BASE_URL}/suggest", params={"q": query, "limit": limit}, timeout=5
            )

            if response.status_code != 200:
                return []

            suggestions = []
            for item in response.json():
                suggestions.append(
                    {
                        "scientificName": item.get("scientificName", ""),
                        "canonicalName": item.get("canonicalName", ""),
                        "rank": item.get("rank", ""),
                        "key": item.get("key", ""),
                        "kingdom": item.get("kingdom", ""),
                    }
                )

            return suggestions

        except Exception as e:
            console.print(f"[yellow]⚠️  GBIF API error: {e}[/yellow]")
            return []

    @classmethod
    def search_locality(cls, query: str, country: str = "Canada") -> List[str]:
        """Get locality suggestions from GBIF occurrence data.

        Args:
            query: Partial locality name
            country: Country filter

        Returns:
            List of common locality names
        """
        # TODO: Implement locality search from GBIF occurrences
        # For now, return common Saskatchewan localities
        common_localities = [
            "Saskatchewan Landing",
            "Val Marie",
            "Swift Current",
            "Regina",
            "Saskatoon",
            "Moose Jaw",
            "Prince Albert",
            "Cypress Hills",
            "Grasslands National Park",
            "Beaver River",
        ]

        if not query:
            return common_localities[:5]

        matches = [loc for loc in common_localities if query.lower() in loc.lower()]
        return matches[:10]


class SpecimenValidator:
    """Core validation and correction logic."""

    def __init__(self, input_file: Path, output_file: Path, images_dir: Optional[Path] = None):
        self.input_file = input_file
        self.output_file = output_file
        self.images_dir = images_dir
        self.specimens = []
        self.corrections = []
        self.current_index = 0

        # Load specimens
        with open(input_file, "r") as f:
            self.specimens = [json.loads(line) for line in f]

    def get_specimen(self, index: int) -> Optional[Dict]:
        """Get specimen at index."""
        if 0 <= index < len(self.specimens):
            return self.specimens[index]
        return None

    def get_image_path(self, specimen: Dict) -> Optional[Path]:
        """Get path to specimen image."""
        if not self.images_dir:
            return None

        image_name = specimen.get("image")
        if not image_name:
            return None

        image_path = self.images_dir / image_name
        if image_path.exists():
            return image_path

        return None

    def save_correction(self, index: int, corrected_dwc: Dict):
        """Save corrected specimen data."""
        specimen = self.specimens[index].copy()
        specimen["dwc"] = corrected_dwc
        specimen["corrected"] = True
        specimen["corrected_by"] = "human_expert"

        self.corrections.append(specimen)

    def save_all(self):
        """Save all corrections to output file."""
        with open(self.output_file, "w") as f:
            for correction in self.corrections:
                f.write(json.dumps(correction) + "\n")

        console.print(
            f"\n[green]✅ Saved {len(self.corrections)} corrections to {self.output_file}[/green]"
        )


class InteractiveCLI:
    """Interactive TUI for specimen correction."""

    def __init__(self, validator: SpecimenValidator):
        self.validator = validator
        self.console = Console()

    def show_image(self, image_path: Path) -> Optional[str]:
        """Show image preview if supported."""
        if not Pixels or not image_path:
            return None

        try:
            img = Image.open(image_path)
            # Resize for terminal display
            img.thumbnail((80, 40))
            return Pixels.from_image(img)
        except Exception:
            return None

    def display_specimen(self, specimen: Dict):
        """Display specimen with extracted fields."""
        dwc = specimen.get("dwc", {})
        confidence = specimen.get("dwc_confidence", {})

        # Create field table
        table = Table(title="Extracted Fields", show_header=True)
        table.add_column("Field", style="cyan", width=25)
        table.add_column("Value", style="white")
        table.add_column("Conf", justify="right", style="yellow", width=6)

        # Key fields first
        key_fields = [
            "catalogNumber",
            "scientificName",
            "recordedBy",
            "recordNumber",
            "eventDate",
            "locality",
            "habitat",
            "stateProvince",
            "country",
        ]

        for field in key_fields:
            if field in dwc:
                value = dwc[field]
                conf = confidence.get(field, 0.0)
                conf_str = f"{conf:.2f}" if conf else "-"

                # Highlight low confidence
                style = "red" if conf < 0.7 else "white"
                table.add_row(field, str(value), conf_str, style=style)

        # Other fields
        other_fields = [k for k in dwc.keys() if k not in key_fields and dwc[k]]
        if other_fields:
            table.add_row("", "", "", style="dim")
            for field in sorted(other_fields):
                value = dwc[field]
                conf = confidence.get(field, 0.0)
                conf_str = f"{conf:.2f}" if conf else "-"
                table.add_row(field, str(value), conf_str)

        return table

    def edit_field(self, field: str, current_value: str) -> str:
        """Edit a single field with autocomplete."""
        console.print(f"\n[cyan]Editing: {field}[/cyan]")
        console.print(f"Current: [white]{current_value}[/white]")

        # Scientific name gets GBIF autocomplete
        if field == "scientificName":
            return self.edit_scientific_name(current_value)

        # Locality gets locality suggestions
        elif field == "locality":
            return self.edit_locality(current_value)

        # Default: simple text input
        else:
            new_value = Prompt.ask("New value (or Enter to keep current)", default=current_value)
            return new_value

    def edit_scientific_name(self, current: str) -> str:
        """Edit scientific name with GBIF autocomplete."""
        query = Prompt.ask("Search GBIF (or Enter to keep current)", default=current)

        if query == current:
            return current

        # Get suggestions
        console.print("\n[yellow]🔍 Searching GBIF...[/yellow]")
        suggestions = GBIFAutocomplete.suggest_scientific_name(query)

        if not suggestions:
            console.print("[red]No matches found[/red]")
            return current

        # Display suggestions
        console.print("\n[cyan]Matches:[/cyan]")
        for i, match in enumerate(suggestions, 1):
            name = match["scientificName"]
            rank = match.get("rank", "")
            kingdom = match.get("kingdom", "")
            console.print(f"  {i}. {name} ({rank}, {kingdom})")

        # Select
        choice = Prompt.ask("Select number (or 0 to keep current, c for custom)", default="0")

        if choice == "0":
            return current
        elif choice.lower() == "c":
            return Prompt.ask("Enter custom value", default=current)
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(suggestions):
                    return suggestions[idx]["scientificName"]
            except ValueError:
                pass

        return current

    def edit_locality(self, current: str) -> str:
        """Edit locality with suggestions."""
        suggestions = GBIFAutocomplete.search_locality(current)

        if suggestions:
            console.print("\n[cyan]Common localities:[/cyan]")
            for i, loc in enumerate(suggestions, 1):
                console.print(f"  {i}. {loc}")

        choice = Prompt.ask("Enter number, custom value, or Enter to keep current", default="0")

        if choice == "0":
            return current

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(suggestions):
                return suggestions[idx]
        except ValueError:
            # Custom value
            return choice if choice else current

        return current

    def review_specimen(self, index: int) -> bool:
        """Review and correct a single specimen.

        Returns:
            True if corrections were saved, False if skipped
        """
        specimen = self.validator.get_specimen(index)
        if not specimen:
            return False

        total = len(self.validator.specimens)

        # Header
        console.clear()
        console.print(Panel(f"[bold]Specimen {index + 1} of {total}[/bold]", style="cyan"))

        # Image preview (if available)
        image_path = self.validator.get_image_path(specimen)
        if image_path:
            pixels = self.show_image(image_path)
            if pixels:
                console.print(pixels)

        # Display extracted fields
        table = self.display_specimen(specimen)
        console.print("\n", table)

        # Menu
        console.print("\n[cyan]Actions:[/cyan]")
        console.print("  [s] Edit scientificName")
        console.print("  [c] Edit catalogNumber")
        console.print("  [r] Edit recordedBy")
        console.print("  [l] Edit locality")
        console.print("  [e] Edit any field")
        console.print("  [a] Accept as-is")
        console.print("  [n] Next (skip)")
        console.print("  [q] Quit and save")

        action = Prompt.ask("\nAction", default="a").lower()

        if action == "q":
            return False

        if action == "n":
            return False

        if action == "a":
            # Save without changes
            self.validator.save_correction(index, specimen["dwc"])
            return True

        # Edit specific field
        dwc = specimen["dwc"].copy()

        field_map = {
            "s": "scientificName",
            "c": "catalogNumber",
            "r": "recordedBy",
            "l": "locality",
        }

        if action in field_map:
            field = field_map[action]
            current = dwc.get(field, "")
            new_value = self.edit_field(field, current)
            dwc[field] = new_value
            self.validator.save_correction(index, dwc)
            return True

        elif action == "e":
            # Edit any field
            field = Prompt.ask("Field name")
            if field in dwc:
                current = dwc.get(field, "")
                new_value = self.edit_field(field, current)
                dwc[field] = new_value
                self.validator.save_correction(index, dwc)
                return True

        return False

    def run(self):
        """Run interactive review session."""
        console.print(
            Panel(
                "[bold cyan]Interactive Specimen Correction Tool[/bold cyan]\n"
                "Review extraction results and make expert corrections.",
                title="Welcome",
            )
        )

        total = len(self.validator.specimens)
        console.print(f"\n📊 Total specimens: {total}")

        if not Confirm.ask("\nStart review?"):
            return

        # Review loop
        for i in range(total):
            saved = self.review_specimen(i)

            if not saved and i < total - 1:
                if not Confirm.ask("Continue to next specimen?"):
                    break

        # Save all corrections
        if self.validator.corrections:
            self.validator.save_all()

            # Show summary
            console.print(
                f"\n[green]✅ Reviewed {len(self.validator.corrections)} / {total} specimens[/green]"
            )


def main():
    parser = argparse.ArgumentParser(
        description="Interactive CLI correction tool with GBIF autocomplete"
    )
    parser.add_argument("--input", type=Path, required=True, help="Input extraction JSONL file")
    parser.add_argument("--output", type=Path, required=True, help="Output corrected JSONL file")
    parser.add_argument("--images", type=Path, help="Directory containing specimen images")

    args = parser.parse_args()

    if not args.input.exists():
        console.print(f"[red]Error: Input file not found: {args.input}[/red]")
        sys.exit(1)

    # Create validator
    validator = SpecimenValidator(args.input, args.output, args.images)

    # Run interactive CLI
    cli = InteractiveCLI(validator)
    cli.run()


if __name__ == "__main__":
    main()
