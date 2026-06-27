"""Source-specific analyzers that augment signature matching.

Signature matching (in :mod:`devops_ai_toolkit.detectors`) finds *known error
patterns*. Analyzers add *structural* insight for a given source kind — for
example, when analyzing a Kubernetes manifest we also run the manifest validator
and fold its best-practice findings into the result. The engine selects the
right analyzer via :func:`get_analyzer`.
"""

from __future__ import annotations

from .base import Analyzer
from .manifest import ManifestAnalyzer
from .registry import get_analyzer
from .terraform import TerraformAnalyzer

__all__ = ["Analyzer", "ManifestAnalyzer", "TerraformAnalyzer", "get_analyzer"]
