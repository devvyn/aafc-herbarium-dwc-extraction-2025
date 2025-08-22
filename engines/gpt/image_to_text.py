from __future__ import annotations

import base64
from importlib import resources
from pathlib import Path
from typing import Dict, Tuple

try:  # optional dependency
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None


def _load_prompt(name: str) -> str:
    return resources.files(__package__).joinpath("prompts", name).read_text(encoding="utf-8")


def image_to_text(image: Path, *, model: str, dry_run: bool = False) -> Tuple[str, Dict[str, float]]:
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
    prompt = _load_prompt("image_to_text.prompt")
    if dry_run or OpenAI is None:
        return "", {"text": 0.0}

    client = OpenAI()
    with image.open("rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    # The exact request structure may vary across OpenAI SDK versions.
    # This implementation targets the Responses API available in the
    # official SDK.  If the API changes, the call below should be
    # updated accordingly.
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

    text = getattr(resp, "output_text", "")
    confidence = float(getattr(resp, "confidence", 1.0))
    return text, {"text": confidence}
