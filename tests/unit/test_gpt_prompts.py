from pathlib import Path
import importlib
import pytest

from engines.errors import EngineError

load_messages = importlib.import_module("engines.gpt.text_to_dwc").load_messages

RESOURCES = Path(__file__).resolve().parents[1] / "resources" / "gpt_prompts"


def test_loads_from_custom_dir() -> None:
    base = RESOURCES / "custom"
    messages = load_messages("text_to_dwc", base)
    expected = [
        {"role": "system", "content": (base / "text_to_dwc.system.prompt").read_text()},
        {"role": "user", "content": (base / "text_to_dwc.user.prompt").read_text()},
    ]
    assert messages == expected


def test_falls_back_to_legacy_file() -> None:
    base = RESOURCES / "legacy"
    messages = load_messages("text_to_dwc", base)
    expected = [{"role": "user", "content": (base / "text_to_dwc.prompt").read_text()}]
    assert messages == expected


def test_defaults_to_package_prompts() -> None:
    messages = load_messages("text_to_dwc")
    cfg = Path("config/prompts")
    expected = [
        {"role": "system", "content": (cfg / "text_to_dwc.system.prompt").read_text()},
        {"role": "user", "content": (cfg / "text_to_dwc.user.prompt").read_text()},
    ]
    assert messages == expected


def test_missing_user_prompt_raises(tmp_path: Path) -> None:
    # Provide only a system prompt; should raise EngineError due to missing user prompt
    prompt_dir = tmp_path
    (prompt_dir / "text_to_dwc.system.prompt").write_text("only system")
    with pytest.raises(EngineError):
        load_messages("text_to_dwc", prompt_dir)
