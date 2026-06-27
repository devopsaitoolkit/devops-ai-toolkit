"""The Python SDK surface.

A thin, documented re-export of the engine and models so integrators can write::

    from devops_ai_toolkit.sdk import AnalysisEngine

    engine = AnalysisEngine()
    result = engine.analyze_file("nova.log")

The very same names are also available directly from the top-level
``devops_ai_toolkit`` package.
"""

from __future__ import annotations

from ..analysis import AnalysisEngine
from ..explainers import ErrorCatalog
from ..models import (
    AnalysisRequest,
    AnalysisResult,
    ExplainResult,
    Technology,
    ValidationResult,
)
from ..output import to_json

__all__ = [
    "AnalysisEngine",
    "AnalysisRequest",
    "AnalysisResult",
    "ErrorCatalog",
    "ExplainResult",
    "Technology",
    "ValidationResult",
    "to_json",
]
