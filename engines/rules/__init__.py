"""Rule-based pattern matching engines for herbarium data extraction.

Provides free, API-less extraction engines using regex patterns and heuristics.
"""

from .text_to_dwc import text_to_dwc
from .. import register_task

# Register rule-based text_to_dwc engine
register_task("text_to_dwc", "rules", __name__, "text_to_dwc")

__all__ = ["text_to_dwc"]
