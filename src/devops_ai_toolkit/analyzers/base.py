"""The analyzer protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..models.analysis import AnalysisResult


@runtime_checkable
class Analyzer(Protocol):
    """Augments an :class:`AnalysisResult` with source-specific structural insight.

    Implementations are pure: they read ``content`` and return a (possibly new)
    result. They must never mutate external state or execute anything.
    """

    def augment(self, result: AnalysisResult, content: str) -> AnalysisResult:
        """Return ``result`` enriched with structural findings for ``content``."""
        ...
