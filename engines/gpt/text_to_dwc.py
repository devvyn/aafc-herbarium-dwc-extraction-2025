from __future__ import annotations


import json
from importlib import resources
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..errors import EngineError
from ..protocols import TextToDwcEngine

try:  # optional dependency
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI: type | None = None  # Explicit: OpenAI may be None if not installed


def load_messages(task: str, prompt_dir: Optional[Path] = None) -> List[Dict[str, str]]:
    base = Path(prompt_dir) if prompt_dir else resources.files("config").joinpath("prompts")
    messages: List[Dict[str, str]] = []
    for role in ("system", "assistant", "user"):
        file = base.joinpath(f"{task}.{role}.prompt")
        if file.is_file():
            messages.append({"role": role, "content": file.read_text(encoding="utf-8")})
    if not messages or messages[-1]["role"] != "user":
        legacy = base.joinpath(f"{task}.prompt")
        if legacy.is_file():
            messages.append({"role": "user", "content": legacy.read_text(encoding="utf-8")})
    if not messages or messages[-1]["role"] != "user":
        raise EngineError("MISSING_PROMPT", f"user prompt for {task} not found")
    return messages


def text_to_dwc(
    text: str,
    *,
    model: str,
    dry_run: bool = False,
    prompt_dir: Optional[Path] = None,
    fields: Optional[List[str]] = None,
) -> Tuple[Dict[str, str], Dict[str, float]]:
    """Map unstructured text to Darwin Core terms using a GPT model.

    The model is expected to return JSON where each key is a Darwin Core
    term mapping to a dictionary containing ``value`` and ``confidence``
    entries.  Any parsing errors result in empty outputs.

    Parameters
    ----------
    text:
        Unstructured text to map.
    model:
        The GPT model name to use.
    dry_run:
        When ``True`` or when the OpenAI SDK is unavailable, no network
        call is performed and empty results are returned.
    prompt_dir:
        Optional directory containing prompt templates.
    fields:
        Optional list of Darwin Core fields to emphasise in the prompt.
    """
    messages = load_messages("text_to_dwc", prompt_dir)
    field_hint = ", ".join(fields) if fields else "required"
    for msg in messages:
        msg["content"] = msg["content"].replace("%FIELD%", field_hint)
    if dry_run:
        return {}, {}
    if OpenAI is None:
        raise EngineError("MISSING_DEPENDENCY", "OpenAI SDK not available")

    client = OpenAI()
    messages[-1]["content"] = f"{messages[-1]['content']}{text}"

    try:
        resp = client.responses.create(model=model, input=messages)
    except Exception as exc:  # pragma: no cover - network issues
        raise EngineError("API_ERROR", str(exc)) from exc
    content = getattr(resp, "output_text", "{}")
    try:
        data = json.loads(content)
    except Exception as exc:
        raise EngineError("PARSE_ERROR", str(exc)) from exc

    dwc = {k: v.get("value", "") for k, v in data.items() if isinstance(v, dict)}
    confidences = {
        k: float(v.get("confidence", 0.0)) for k, v in data.items() if isinstance(v, dict)
    }
    return dwc, confidences


# Static type checking helper
_TEXT_TO_DWC_CHECK: TextToDwcEngine = text_to_dwc
