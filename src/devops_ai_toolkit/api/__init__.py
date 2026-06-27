"""The FastAPI REST interface (optional ``api`` extra)."""

from __future__ import annotations

__all__ = ["app"]


def __getattr__(name: str) -> object:
    """Lazily expose ``app`` so importing the package never requires FastAPI."""
    if name == "app":
        from .app import app

        return app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
