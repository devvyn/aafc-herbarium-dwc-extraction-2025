"""Evaluate GPT prompt template coverage."""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from engines.gpt.image_to_text import load_messages

REQUIRED_PLACEHOLDERS = {
    "image_to_text": ["%LANG%"],
    "text_to_dwc": ["%FIELD%"],
    "image_to_dwc": ["%FIELD%"],
}


def evaluate() -> int:
    """Return 0 if all required placeholders are present."""
    missing: list[str] = []
    for task, placeholders in REQUIRED_PLACEHOLDERS.items():
        messages = load_messages(task)
        content = "\n".join(m["content"] for m in messages)
        for token in placeholders:
            if token not in content:
                missing.append(f"{task}: {token}")
    if missing:
        for m in missing:
            print(f"missing placeholder {m}")
        return 1
    print("all prompts contain required placeholders")
    return 0


if __name__ == "__main__":
    raise SystemExit(evaluate())
