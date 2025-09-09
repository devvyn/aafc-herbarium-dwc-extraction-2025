from engines.gpt.image_to_text import load_messages

REQUIRED_PLACEHOLDERS = {
    "image_to_text": ["%LANG%"],
    "text_to_dwc": ["%FIELD%"],
    "image_to_dwc": ["%FIELD%"],
}


def test_prompts_contain_required_placeholders() -> None:
    for task, placeholders in REQUIRED_PLACEHOLDERS.items():
        messages = load_messages(task)
        content = "\n".join(m["content"] for m in messages)
        for placeholder in placeholders:
            assert placeholder in content, (
                f"{placeholder} missing from {task} prompts"
            )

