from importlib import import_module
from typing import Any

_TASKS = {
    "image_to_text": ("engines.gpt", "image_to_text"),
    "text_to_dwc": ("engines.gpt", "text_to_dwc"),
}


def dispatch(task: str, *args: Any, **kwargs: Any) -> Any:
    """Dispatch a task to the appropriate engine function."""
    try:
        module_name, func_name = _TASKS[task]
    except KeyError as exc:
        raise ValueError(f"Unknown task: {task}") from exc
    module = import_module(module_name)
    func = getattr(module, func_name)
    return func(*args, **kwargs)

__all__ = ["dispatch"]
