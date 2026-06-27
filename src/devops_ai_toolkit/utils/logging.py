"""Lightweight, Rich-aware logging setup."""

from __future__ import annotations

import logging
from functools import cache

from rich.logging import RichHandler


@cache
def get_logger(name: str = "devops_ai_toolkit") -> logging.Logger:
    """Return a configured logger that renders nicely in the terminal."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = RichHandler(rich_tracebacks=True, show_path=False, markup=True)
        handler.setFormatter(logging.Formatter("%(message)s", datefmt="[%X]"))
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
        logger.propagate = False
    return logger
