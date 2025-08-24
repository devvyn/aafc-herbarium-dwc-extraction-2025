from importlib import import_module
from typing import Any

_TASKS = {
    "image_to_text": {
        "gpt": ("engines.gpt", "image_to_text"),
        "vision": ("engines.vision_swift", "image_to_text"),
        "tesseract": ("engines.tesseract", "image_to_text"),
    },
    "text_to_dwc": {
        "gpt": ("engines.gpt", "text_to_dwc"),
    },
}


def dispatch(task: str, *args: Any, engine: str = "gpt", **kwargs: Any) -> Any:
    """Dispatch a task to the appropriate engine function."""
    try:
        module_name, func_name = _TASKS[task][engine]
    except KeyError as exc:
        raise ValueError(f"Unknown task or engine: {task}/{engine}") from exc
    module = import_module(module_name)
    func = getattr(module, func_name)
    return func(*args, **kwargs)

__all__ = ["dispatch"]
