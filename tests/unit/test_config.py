import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cli import load_config


def test_load_config_merge(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text("""
[ocr]
preferred_engine = "tesseract"
[gpt]
model = "gpt-test"
""")
    cfg = load_config(cfg_path)
    assert cfg["ocr"]["preferred_engine"] == "tesseract"
    assert cfg["gpt"]["model"] == "gpt-test"
    # default from base config remains
    assert cfg["ocr"]["allow_gpt"] is True
