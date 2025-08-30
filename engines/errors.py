from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EngineError(Exception):
    """Standard error raised by engine adapters.

    Parameters
    ----------
    code:
        Short machine readable error code.
    message:
        Human readable error message.
    """

    code: str
    message: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.code}: {self.message}"


__all__ = ["EngineError"]
