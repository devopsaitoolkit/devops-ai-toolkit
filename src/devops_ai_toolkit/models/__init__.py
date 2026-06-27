"""Typed domain models for the DevOps AI Toolkit.

Importing from :mod:`devops_ai_toolkit.models` gives you the full, stable
vocabulary shared by the engine and every interface.
"""

from __future__ import annotations

from .analysis import (
    AnalysisRequest,
    AnalysisResult,
    DiagnosticCommand,
    Enrichment,
    ExplainResult,
    Reference,
    RootCause,
    SuggestedFix,
    ValidationIssue,
    ValidationResult,
    Warning,
)
from .enums import ConfidenceBand, Severity, SourceKind, Technology
from .knowledge import CauseTemplate, MatchSpec, Signature, SignatureMatch

__all__ = [
    "AnalysisRequest",
    "AnalysisResult",
    "CauseTemplate",
    "ConfidenceBand",
    "DiagnosticCommand",
    "Enrichment",
    "ExplainResult",
    "MatchSpec",
    "Reference",
    "RootCause",
    "Severity",
    "Signature",
    "SignatureMatch",
    "SourceKind",
    "SuggestedFix",
    "Technology",
    "ValidationIssue",
    "ValidationResult",
    "Warning",
]
