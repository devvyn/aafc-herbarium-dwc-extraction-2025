import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import qc
from cli import setup_run


def test_custom_gbif_endpoints(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
        """
[gbif]
species_match_endpoint = "https://example.org/species"
reverse_geocode_endpoint = "https://example.org/geocode"
"""
    )

    setup_run(tmp_path, cfg_path, None)

    assert qc.GBIF_SPECIES_MATCH_ENDPOINT == "https://example.org/species"
    assert qc.GBIF_REVERSE_GEOCODE_ENDPOINT == "https://example.org/geocode"
