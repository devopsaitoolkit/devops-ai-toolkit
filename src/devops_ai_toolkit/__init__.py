"""DevOps AI Toolkit — read-only, AI-powered DevOps troubleshooting.

One shared :class:`AnalysisEngine` powers the CLI, the Python SDK and the REST
API. The engine inspects logs, manifests, Terraform, and command output and
returns ranked root causes, read-only diagnostic commands, suggested fixes,
references and prevention advice. It is offline-first and deterministic; LLM
providers are optional enrichment behind a vendor-agnostic adapter interface.

Quick start::

    from devops_ai_toolkit import AnalysisEngine

    engine = AnalysisEngine()
    result = engine.analyze_file("nova.log")
    print(result.summary)

See https://devopsaitoolkit.com for tutorials and troubleshooting guides.
"""

from __future__ import annotations

from ._version import __version__
from .analysis import AnalysisEngine
from .explainers import ErrorCatalog
from .models import (
    AnalysisRequest,
    AnalysisResult,
    ExplainResult,
    SourceKind,
    Technology,
    ValidationResult,
)
from .plugins import (
    AnalyzerPlugin,
    KnowledgeBackedPlugin,
    PluginManager,
    PluginMetadata,
)

__all__ = [
    "AnalysisEngine",
    "AnalysisRequest",
    "AnalysisResult",
    "AnalyzerPlugin",
    "ErrorCatalog",
    "ExplainResult",
    "KnowledgeBackedPlugin",
    "PluginManager",
    "PluginMetadata",
    "SourceKind",
    "Technology",
    "ValidationResult",
    "__version__",
]
