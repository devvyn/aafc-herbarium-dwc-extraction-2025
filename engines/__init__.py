"""Engine registration and dispatch helpers.

This module exposes a small plugin system that allows OCR/DWC engines to
register the tasks that they implement.  Built-in engines register themselves
when imported, and additional engines can be discovered via the
``herbarium.engines`` entry-point group.
"""

from importlib import import_module, metadata
from typing import Any, Dict, Tuple

# Registry mapping task -> engine -> (module, function)
_REGISTRY: Dict[str, Dict[str, Tuple[str, str]]] = {}


def register_task(task: str, engine: str, module: str, func: str) -> None:
    """Register ``func`` from ``module`` as the implementation of a task.

    Parameters
    ----------
    task:
        Name of the task (e.g., ``"image_to_text"``).
    engine:
        Engine identifier (e.g., ``"gpt"`` or ``"tesseract"``).
    module:
        Import path of the module containing the function.
    func:
        Name of the function implementing the task.
    """

    _REGISTRY.setdefault(task, {})[engine] = (module, func)


def _discover_entry_points() -> None:
    """Load engines exposed via the ``herbarium.engines`` entry point."""

    try:  # Python 3.10+
        eps = metadata.entry_points().select(group="herbarium.engines")
    except AttributeError:  # pragma: no cover - older Python
        eps = metadata.entry_points().get("herbarium.engines", [])
    for ep in eps:
        ep.load()  # Importing registers the engine


# Import built-in engines so they register themselves on module import.
for _mod in ("gpt", "vision_swift", "tesseract"):
    try:
        import_module(f"{__name__}.{_mod}")
    except Exception:  # pragma: no cover - optional deps may be missing
        pass

_discover_entry_points()


def dispatch(task: str, *args: Any, engine: str = "gpt", **kwargs: Any) -> Any:
    """Dispatch a task to the requested engine.

    Raises
    ------
    ValueError
        If the task or engine is unknown.
    """

    if task not in _REGISTRY:
        raise ValueError(f"Unknown task: {task}")
    engines = _REGISTRY[task]
    if engine not in engines:
        available = ", ".join(sorted(engines))
        raise ValueError(
            f"Engine '{engine}' unavailable for task '{task}'. Available: {available}"
        )
    module_name, func_name = engines[engine]
    module = import_module(module_name)
    func = getattr(module, func_name)
    return func(*args, **kwargs)


__all__ = ["dispatch", "register_task"]

