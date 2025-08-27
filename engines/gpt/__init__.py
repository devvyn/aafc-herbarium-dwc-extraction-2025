from .image_to_text import image_to_text
from .text_to_dwc import text_to_dwc

from .. import register_task

register_task("image_to_text", "gpt", __name__, "image_to_text")
register_task("text_to_dwc", "gpt", __name__, "text_to_dwc")

__all__ = ["image_to_text", "text_to_dwc"]
