"""Engine registration and dispatch helpers.

This module exposes a small plugin system that allows OCR/DWC engines to
register the tasks that they implement.  Built-in engines register themselves
when imported, and additional engines can be discovered via the
``herbarium.engines`` entry-point group.
"""

from importlib import import_module, metadata, resources
from pathlib import Path
from typing import Any, Dict, Tuple, Callable, List, Optional

# Registry mapping task -> engine -> (module, function)
_REGISTRY: Dict[str, Dict[str, Tuple[str, str]]] = {}

# Fallback policy registry mapping engine -> policy function
# The policy returns ``(text, confidences, engine, engine_version)``
_FALLBACK_POLICIES: Dict[
    str,
    Callable[[Path, str, List[float], Dict[str, Any]], Tuple[str, List[float], str, Optional[str]]],
] = {}


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


def register_fallback_policy(
    engine: str,
    func: Callable[
        [Path, str, List[float], Dict[str, Any]], Tuple[str, List[float], str, Optional[str]]
    ],
) -> None:
    """Register a fallback policy for an engine.

    Policies receive the image path, extracted text, token confidences and the
    full configuration dictionary.  They return a tuple containing the final
    text, confidences, engine name and optional engine version.
    """

    _FALLBACK_POLICIES[engine] = func


def get_fallback_policy(
    engine: str,
) -> Optional[
    Callable[[Path, str, List[float], Dict[str, Any]], Tuple[str, List[float], str, Optional[str]]]
]:
    """Return the registered fallback policy for ``engine`` if any."""

    return _FALLBACK_POLICIES.get(engine)


def available_engines(task: str) -> List[str]:
    """Return a sorted list of engines available for ``task``."""

    return sorted(_REGISTRY.get(task, {}))


def _discover_entry_points() -> None:
    """Load engines exposed via the ``herbarium.engines`` entry point."""

    try:  # Python 3.10+
        eps = metadata.entry_points().select(group="herbarium.engines")
    except AttributeError:  # pragma: no cover - older Python
        eps = metadata.entry_points().get("herbarium.engines", [])
    for ep in eps:
        ep.load()  # Importing registers the engine


# Import built-in engines so they register themselves on module import.
for _mod in ("gpt", "vision_swift", "tesseract", "paddleocr", "multilingual"):
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
        raise ValueError(f"Engine '{engine}' unavailable for task '{task}'. Available: {available}")
    module_name, func_name = engines[engine]
    module = import_module(module_name)
    func = getattr(module, func_name)
    return func(*args, **kwargs)


def _register_default_fallbacks() -> None:
    """Register fallback policies for built-in engines."""

    def _gpt_fallback(engine_name: str):
        def _policy(
            image: Path,
            text: str,
            confidences: List[float],
            cfg: Dict[str, Any],
        ) -> Tuple[str, List[float], str, Optional[str]]:
            ocr_cfg = cfg.get("ocr", {})
            gpt_cfg = cfg.get("gpt", {})
            image_conf = sum(confidences) / len(confidences) if confidences else 0.0
            if (
                ocr_cfg.get("allow_gpt")
                and (not text or image_conf < ocr_cfg.get("confidence_threshold", 0.0))
                and image_conf < gpt_cfg.get("fallback_threshold", 1.0)
            ):
                available = available_engines("image_to_text")
                enabled = ocr_cfg.get("enabled_engines")
                if enabled:
                    available = [e for e in available if e in enabled]
                if "gpt" not in available:
                    return text, confidences, engine_name, None
                prompt_dir = resources.files("config").joinpath(
                    gpt_cfg.get("prompt_dir", "prompts")
                )
                text, conf = dispatch(
                    "image_to_text",
                    image=image,
                    engine="gpt",
                    model=gpt_cfg["model"],
                    dry_run=gpt_cfg["dry_run"],
                    prompt_dir=prompt_dir,
                )
                return text, conf, "gpt", gpt_cfg["model"]
            return text, confidences, engine_name, None

        return _policy

    for engine_name in ("vision", "tesseract"):
        register_fallback_policy(engine_name, _gpt_fallback(engine_name))


_register_default_fallbacks()

# Import built-in engines to trigger registration
from . import rules  # noqa: E402, F401 - imported for side effects (registration)

__all__ = [
    "dispatch",
    "register_task",
    "available_engines",
    "register_fallback_policy",
    "get_fallback_policy",
]
