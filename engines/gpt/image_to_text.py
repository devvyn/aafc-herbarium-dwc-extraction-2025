from __future__ import annotations


import base64
from importlib import resources
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..errors import EngineError
from ..protocols import ImageToTextEngine

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


def image_to_text(
    image: Path,
    *,
    model: str,
    dry_run: bool = False,
    prompt_dir: Optional[Path] = None,
    langs: Optional[List[str]] = None,
) -> Tuple[str, List[float]]:
    """Use a GPT model to extract text from an image.

    Parameters
    ----------
    image:
        Path to the image on disk.
    model:
        The GPT model name to use.
    dry_run:
        When ``True`` or when the OpenAI SDK is unavailable, no network
        call is performed and an empty result is returned.
    langs:
        Optional language hints appended as a system message. When omitted the
        model infers the language automatically.
    """
    messages = load_messages("image_to_text", prompt_dir)
    lang_hint = ", ".join(langs) if langs else None
    if lang_hint:
        messages.insert(0, {"role": "system", "content": f"Languages: {lang_hint}"})
    replace_lang = lang_hint or "the source language"
    for msg in messages:
        msg["content"] = msg["content"].replace("%LANG%", replace_lang)
    if dry_run:
        return "", []
    if OpenAI is None:
        raise EngineError("MISSING_DEPENDENCY", "OpenAI SDK not available")

    client = OpenAI()
    with image.open("rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    # The exact request structure may vary across OpenAI SDK versions.
    # This implementation targets the Responses API available in the
    # official SDK.  If the API changes, the call below should be
    # updated accordingly.
    messages[-1]["content"] = [
        {"type": "text", "text": messages[-1]["content"]},
        {"type": "image", "image": {"b64": b64}},
    ]

    try:
        resp = client.responses.create(model=model, input=messages)
    except Exception as exc:  # pragma: no cover - network issues
        raise EngineError("API_ERROR", str(exc)) from exc

    text = getattr(resp, "output_text", "")
    confidence = float(getattr(resp, "confidence", 1.0))
    return text, [confidence]


# Static type checking helper
_IMAGE_TO_TEXT_CHECK: ImageToTextEngine = image_to_text
