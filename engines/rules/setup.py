"""Setup for rule-based extraction engines."""


def register_engines():
    """Register text_to_dwc engine."""
    from . import text_to_dwc

    # Register the function as an available engine
    import sys

    if "engines" in sys.modules:
        engines_module = sys.modules["engines"]
        if hasattr(engines_module, "_register_engine"):
            engines_module._register_engine("text_to_dwc", "rules", text_to_dwc.text_to_dwc)
