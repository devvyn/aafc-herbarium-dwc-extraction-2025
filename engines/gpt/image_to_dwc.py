from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Dict, Tuple

from ..errors import EngineError
from ..protocols import ImageToDwcEngine

try:  # optional dependency
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None


def image_to_dwc(
    image: Path, instructions: str, *, model: str, dry_run: bool = False
) -> Tuple[Dict[str, str], Dict[str, float]]:
    """Map an image and instructions to Darwin Core terms using a GPT model.

    The model is expected to return JSON where each key is a Darwin Core term
    mapping to a dictionary containing ``value`` and ``confidence`` entries.
    Any parsing errors result in empty outputs.
    """
    if dry_run:
        return {}, {}
    if OpenAI is None:
        raise EngineError("MISSING_DEPENDENCY", "OpenAI SDK not available")

    client = OpenAI()
    with image.open("rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    try:
        resp = client.responses.create(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": instructions},
                        {"type": "image", "image": {"b64": b64}},
                    ],
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
    confidences = {
        k: float(v.get("confidence", 0.0)) for k, v in data.items() if isinstance(v, dict)
    }
    return dwc, confidences


# Static type checking helper
_IMAGE_TO_DWC_CHECK: ImageToDwcEngine = image_to_dwc
