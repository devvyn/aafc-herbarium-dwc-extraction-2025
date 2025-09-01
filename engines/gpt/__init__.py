from .image_to_text import image_to_text
from .text_to_dwc import text_to_dwc
from .image_to_dwc import image_to_dwc

from .. import register_task

try:  # load environment variables from .env if available
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - optional dependency
    pass

register_task("image_to_text", "gpt", __name__, "image_to_text")
register_task("text_to_dwc", "gpt", __name__, "text_to_dwc")
register_task("image_to_dwc", "gpt", __name__, "image_to_dwc")

__all__ = ["image_to_text", "text_to_dwc", "image_to_dwc"]
