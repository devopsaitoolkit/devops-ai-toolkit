"""The :class:`AnalyzerPlugin` abstract base class — the plugin contract.

Every technology the toolkit understands is an *independent plugin* implementing
this interface. The core engine never contains technology-specific logic; it
discovers plugins and delegates to them. Third-party developers implement this
ABC (usually by subclassing :class:`KnowledgeBackedPlugin`) and ship it as an
installable package exposing a ``devops_ai_toolkit.plugins`` entry point.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models.analysis import AnalysisResult, ExplainResult, ValidationResult
from ..models.enums import SourceKind, Technology
from ..models.knowledge import Signature
from .metadata import PluginMetadata


class AnalyzerPlugin(ABC):
    """Abstract interface every analyzer plugin must implement."""

    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return the plugin's self-describing metadata."""

    @property
    def name(self) -> str:
        """The plugin's unique name."""
        return self.metadata().name

    @property
    def version(self) -> str:
        """The plugin's version string."""
        return self.metadata().version

    @abstractmethod
    def supports(
        self,
        content: str,
        *,
        technology: Technology | None = None,
        source_kind: SourceKind | None = None,
        filename: str | None = None,
    ) -> bool:
        """Return True if this plugin can analyze the given input."""

    @abstractmethod
    def analyze(
        self,
        content: str,
        *,
        technology: Technology | None = None,
        source_kind: SourceKind | None = None,
        filename: str | None = None,
        max_root_causes: int = 5,
    ) -> AnalysisResult:
        """Analyze ``content`` and return ranked findings."""

    @abstractmethod
    def validate(self, content: str, *, filename: str | None = None) -> ValidationResult:
        """Validate a manifest/config this plugin understands (read-only)."""

    @abstractmethod
    def explain(self, query: str) -> ExplainResult | None:
        """Explain a named error this plugin knows about, or None."""

    @abstractmethod
    def extract_errors(self, content: str) -> list[str]:
        """Return error lines/messages found in ``content``."""

    @abstractmethod
    def extract_warnings(self, content: str) -> list[str]:
        """Return warning lines/messages found in ``content``."""

    @abstractmethod
    def extract_resources(self, content: str) -> list[str]:
        """Return resource identifiers referenced in ``content``."""

    @abstractmethod
    def extract_recommendations(self, result: AnalysisResult) -> list[str]:
        """Return actionable recommendations derived from a result."""

    def signatures(self) -> list[Signature]:
        """Return the knowledge-base signatures this plugin contributes.

        Plugins that do not use the signature mechanism return an empty list.
        Default is empty so the method is optional for custom plugins.
        """
        return []
