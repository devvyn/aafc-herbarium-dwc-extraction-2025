from __future__ import annotations


import json
from importlib import resources
from typing import Dict, Tuple

from ..errors import EngineError
from ..protocols import TextToDwcEngine

try:  # optional dependency
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None


def _load_prompt(name: str) -> str:
    return resources.files(__package__).joinpath("prompts", name).read_text(encoding="utf-8")


def text_to_dwc(text: str, *, model: str, dry_run: bool = False) -> Tuple[Dict[str, str], Dict[str, float]]:
    """Map unstructured text to Darwin Core terms using a GPT model.

    The model is expected to return JSON where each key is a Darwin Core
    term mapping to a dictionary containing ``value`` and ``confidence``
    entries.  Any parsing errors result in empty outputs.
    """
    prompt = _load_prompt("text_to_dwc.prompt")
    if dry_run:
        return {}, {}
    if OpenAI is None:
        raise EngineError("MISSING_DEPENDENCY", "OpenAI SDK not available")

    client = OpenAI()
    try:
        resp = client.responses.create(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": f"{prompt}{text}"}],
                }
            ],
        )
    except Exception as exc:  # pragma: no cover - network issues
        raise EngineError("API_ERROR", str(exc)) from exc
    content = getattr(resp, "output_text", "{}")
    try:
        data = json.loads(content)
    except Exception as exc:
        raise EngineError("PARSE_ERROR", str(exc)) from exc

    dwc = {k: v.get("value", "") for k, v in data.items() if isinstance(v, dict)}
    confidences = {k: float(v.get("confidence", 0.0)) for k, v in data.items() if isinstance(v, dict)}
    return dwc, confidences


# Static type checking helper
_TEXT_TO_DWC_CHECK: TextToDwcEngine = text_to_dwc
