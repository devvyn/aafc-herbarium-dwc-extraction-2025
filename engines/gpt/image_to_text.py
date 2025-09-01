from __future__ import annotations


import base64
from importlib import resources
from pathlib import Path
from typing import List, Tuple, Optional

from ..errors import EngineError
from ..protocols import ImageToTextEngine

try:  # optional dependency
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None


def _load_prompt(name: str, prompt_dir: Optional[Path] = None) -> str:
    if prompt_dir:
        return (Path(prompt_dir) / name).read_text(encoding="utf-8")
    return resources.files("config").joinpath("prompts", name).read_text(encoding="utf-8")


def image_to_text(
    image: Path,
    *,
    model: str,
    dry_run: bool = False,
    prompt_dir: Optional[Path] = None,
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
    """
    prompt = _load_prompt("image_to_text.prompt", prompt_dir)
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
    try:
        resp = client.responses.create(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image", "image": {"b64": b64}},
                    ],
                }
            ],
        )
    except Exception as exc:  # pragma: no cover - network issues
        raise EngineError("API_ERROR", str(exc)) from exc

    text = getattr(resp, "output_text", "")
    confidence = float(getattr(resp, "confidence", 1.0))
    return text, [confidence]


# Static type checking helper
_IMAGE_TO_TEXT_CHECK: ImageToTextEngine = image_to_text
