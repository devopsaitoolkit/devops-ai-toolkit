"""Shared FastAPI dependencies."""

from __future__ import annotations

from functools import lru_cache

from ..analysis import AnalysisEngine


@lru_cache(maxsize=1)
def get_engine() -> AnalysisEngine:
    """Provide a process-wide engine instance (cached)."""
    return AnalysisEngine()
