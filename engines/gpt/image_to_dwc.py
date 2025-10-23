from __future__ import annotations

import base64
import json
from importlib import resources
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..errors import EngineError
from ..protocols import ImageToDwcEngine

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


def image_to_dwc(
    image: Path,
    instructions: str,
    *,
    model: str,
    dry_run: bool = False,
    prompt_dir: Optional[Path] = None,
) -> Tuple[Dict[str, str], Dict[str, float]]:
    """Map an image and instructions to Darwin Core terms using a GPT model.

    The model is expected to return JSON where each key is a Darwin Core term
    mapping to a dictionary containing ``value`` and ``confidence`` entries.
    Any parsing errors result in empty outputs.

    Parameters
    ----------
    image:
        Path to the image on disk.
    instructions:
        The prompt template name (e.g., "image_to_dwc_v2").
    model:
        The GPT model name to use.
    dry_run:
        When ``True``, no network call is performed and an empty result is returned.
    prompt_dir:
        Optional directory containing prompt files.
    """
    if dry_run:
        return {}, {}
    if OpenAI is None:
        raise EngineError("MISSING_DEPENDENCY", "OpenAI SDK not available")

    # Load prompt messages from files
    messages = load_messages(instructions, prompt_dir)

    client = OpenAI()
    with image.open("rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    # Convert last message to vision format
    messages[-1]["content"] = [
        {"type": "text", "text": messages[-1]["content"]},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
    ]

    try:
        resp = client.chat.completions.create(
            model=model, messages=messages, response_format={"type": "json_object"}
        )
    except Exception as exc:  # pragma: no cover - network issues
        raise EngineError("API_ERROR", str(exc)) from exc

    content = resp.choices[0].message.content or "{}"
    try:
        data = json.loads(content)
        if not isinstance(data, dict):
            raise EngineError("PARSE_ERROR", "Response is not a JSON object")
    except Exception as exc:
        raise EngineError("PARSE_ERROR", str(exc)) from exc

    dwc = {k: v.get("value", "") for k, v in data.items() if isinstance(v, dict)}
    confidences = {
        k: float(v.get("confidence", 0.0)) for k, v in data.items() if isinstance(v, dict)
    }
    return dwc, confidences


# Static type checking helper
_IMAGE_TO_DWC_CHECK: ImageToDwcEngine = image_to_dwc
