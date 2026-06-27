"""The :class:`AnalysisEngine` — every interface calls this and nothing else.

The engine contains **no technology-specific logic**. It discovers plugins via a
:class:`~devops_ai_toolkit.plugins.manager.PluginManager`, matches input against
the signatures those plugins own, and delegates manifest validation to the plugin
that owns the technology. Adding support for a new technology means installing a
plugin — never editing this file.

The engine is **read-only**: it inspects text and emits guidance. It never
executes commands, mutates files, or touches infrastructure.
"""

from __future__ import annotations

from pathlib import Path

from ..detectors.matcher import SignatureMatcher
from ..knowledge.loader import KnowledgeBase
from ..models.analysis import (
    AnalysisRequest,
    AnalysisResult,
    Enrichment,
    ExplainResult,
    RootCause,
    ValidationResult,
    Warning,
)
from ..models.enums import Severity, SourceKind, Technology
from ..models.knowledge import Signature
from ..plugins.manager import PluginManager
from ..prompts.enrichment import ENRICHMENT_SYSTEM_PROMPT, build_enrichment_prompt
from ..providers.base import AIProvider, CompletionRequest, NullProvider
from ..providers.registry import get_provider
from ..utils.config import Settings, get_settings
from ..utils.logging import get_logger
from ..utils.text import (
    detect_source_kind,
    detect_technology,
    technology_for_source_kind,
    truncate,
)
from ..validators.yaml_validator import validate_yaml
from .assembly import assemble_result, merge_validation

_logger = get_logger(__name__)

_VALIDATABLE = (
    SourceKind.YAML,
    SourceKind.KUBERNETES_MANIFEST,
    SourceKind.TERRAFORM,
    SourceKind.COMPOSE,
)


class AnalysisEngine:
    """Stateless, dependency-injected façade over the plugin-driven pipeline.

    Args:
        knowledge_base: Override the aggregate signature set (mainly for tests).
        provider: AI provider for optional enrichment. Defaults to the configured
            one (offline ``NullProvider`` when nothing is set up).
        settings: Resolved runtime settings. Defaults to environment-derived.
        plugin_manager: Source of plugins. Defaults to auto-discovery of all
            built-in and installed third-party plugins.
    """

    def __init__(
        self,
        knowledge_base: KnowledgeBase | None = None,
        provider: AIProvider | None = None,
        settings: Settings | None = None,
        plugin_manager: PluginManager | None = None,
    ) -> None:
        """Wire the engine's collaborators, all overridable for testing."""
        self.settings = settings or get_settings()
        self.plugins = plugin_manager or PluginManager.create_default()
        self.knowledge_base = knowledge_base or self.plugins.aggregate_knowledge_base()
        self.provider = provider or get_provider(settings=self.settings)
        self._matcher = SignatureMatcher(self.knowledge_base)

    # ------------------------------------------------------------------ #
    # Public API — mirrored by the SDK, CLI and REST API.                #
    # ------------------------------------------------------------------ #

    def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        """Run the full analysis pipeline for a structured request."""
        content = truncate(request.content, self.settings.max_input_chars)
        technology = request.technology or detect_technology(content, request.filename)
        source_kind = request.source_kind or detect_source_kind(content, request.filename)

        matches = self._matcher.match(content, technology)
        result = assemble_result(
            matches=matches,
            technology=technology,
            source_kind=source_kind,
            max_root_causes=request.max_root_causes,
            signatures_evaluated=len(self.knowledge_base),
        )

        # Delegate structural validation to the plugin that owns the technology.
        if source_kind in _VALIDATABLE:
            plugin = self.plugins.plugin_for_technology(technology)
            if plugin is not None:
                merge_validation(result, plugin.validate(content, filename=request.filename))

        if request.enrich:
            result = self._maybe_enrich(result, content)
        return result

    def analyze_text(
        self,
        content: str,
        *,
        technology: Technology | None = None,
        source_kind: SourceKind | None = None,
        filename: str | None = None,
        enrich: bool = False,
    ) -> AnalysisResult:
        """Analyze a raw string. Convenience wrapper over :meth:`analyze`."""
        return self.analyze(
            AnalysisRequest(
                content=content,
                technology=technology,
                source_kind=source_kind,
                filename=filename,
                enrich=enrich,
            )
        )

    def analyze_file(self, path: str | Path, *, enrich: bool = False) -> AnalysisResult:
        """Read a file from disk and analyze it (the only filesystem read)."""
        file_path = Path(path)
        content = file_path.read_text(encoding="utf-8", errors="replace")
        return self.analyze_text(content, filename=file_path.name, enrich=enrich)

    def analyze_yaml(self, content: str, *, enrich: bool = False) -> AnalysisResult:
        """Analyze YAML/manifest content, hinting the source kind."""
        return self.analyze_text(content, source_kind=SourceKind.YAML, enrich=enrich)

    def analyze_terraform(self, content: str, *, enrich: bool = False) -> AnalysisResult:
        """Analyze Terraform content, hinting the technology and source kind."""
        return self.analyze_text(
            content,
            technology=Technology.TERRAFORM,
            source_kind=SourceKind.TERRAFORM,
            enrich=enrich,
        )

    def explain_error(self, query: str) -> ExplainResult:
        """Explain a named error (e.g. ``CrashLoopBackOff``) from the knowledge base."""
        signature = self._best_signature_for_query(query)
        if signature is None:
            return ExplainResult(
                query=query,
                technology=detect_technology(query),
                title=query,
                summary=(
                    "No exact knowledge-base entry matched. Try `analyze` on the raw "
                    "log/output, or browse more guides at https://devopsaitoolkit.com/blog."
                ),
                matched=False,
            )
        return ExplainResult(
            query=query,
            technology=signature.technology,
            title=signature.title,
            summary=signature.summary,
            root_causes=[_cause_to_model(c) for c in signature.root_causes],
            diagnostic_commands=list(signature.diagnostic_commands),
            suggested_fixes=list(signature.suggested_fixes),
            references=list(signature.references),
            best_practices=list(signature.best_practices),
        )

    def validate_manifest(
        self,
        content: str,
        *,
        technology: Technology | None = None,
        source_kind: SourceKind | None = None,
        filename: str | None = None,
    ) -> ValidationResult:
        """Validate a manifest by delegating to the owning plugin (read-only)."""
        tech = technology or detect_technology(content, filename)
        kind = source_kind or detect_source_kind(content, filename)
        if tech is Technology.UNKNOWN:
            tech = technology_for_source_kind(kind) or tech
        plugin = self.plugins.plugin_for_technology(tech) or self.plugins.plugin_for(
            content, technology=tech, source_kind=kind, filename=filename
        )
        if plugin is not None:
            return plugin.validate(content, filename=filename)
        return validate_yaml(content)

    # ------------------------------------------------------------------ #
    # Internals                                                          #
    # ------------------------------------------------------------------ #

    def _maybe_enrich(self, result: AnalysisResult, raw_input: str) -> AnalysisResult:
        """Attach LLM narrative when a provider is available; otherwise no-op."""
        if isinstance(self.provider, NullProvider) or not self.provider.available():
            _logger.info("Enrichment requested but no AI provider is available; skipping.")
            result.warnings.append(_enrichment_unavailable_warning())
            return result
        try:
            prompt = build_enrichment_prompt(result, raw_input, self.settings.max_input_chars // 4)
            text = self.provider.complete(
                CompletionRequest(system=ENRICHMENT_SYSTEM_PROMPT, prompt=prompt)
            )
        except RuntimeError as exc:  # provider/network failure must not break analysis
            _logger.warning("Enrichment failed: %s", exc)
            return result

        narrative, extra = _split_enrichment(text)
        result.enrichment = Enrichment(
            provider=self.provider.name,
            model=self.provider.model,
            narrative=narrative,
            additional_causes=extra,
        )
        return result

    def _best_signature_for_query(self, query: str) -> Signature | None:
        """Find the signature that best explains a free-text error query."""
        direct = self.knowledge_base.get(query.strip())
        if direct is not None:
            return direct
        hits = self.knowledge_base.search(query)
        if hits:
            return hits[0]
        matches = self._matcher.match(query, detect_technology(query), limit=1)
        return matches[0].signature if matches else None


# ---------------------------------------------------------------------- #
# Module-level helpers (pure functions, easy to test).                   #
# ---------------------------------------------------------------------- #


def _cause_to_model(cause: object) -> RootCause:
    """Convert a knowledge ``CauseTemplate`` into a :class:`RootCause`."""
    return RootCause(
        title=getattr(cause, "title", ""),
        description=getattr(cause, "description", ""),
        confidence=getattr(cause, "confidence", 0.5),
        category=getattr(cause, "category", "general"),
    )


def _enrichment_unavailable_warning() -> Warning:
    """Build the warning shown when enrichment is requested but unavailable."""
    return Warning(
        message=(
            "AI enrichment was requested but no provider is configured. "
            "Returned deterministic results only."
        ),
        severity=Severity.LOW,
    )


def _split_enrichment(text: str) -> tuple[str, list[str]]:
    """Separate the narrative from ``CAUSE:``-prefixed extra hypotheses."""
    narrative_lines: list[str] = []
    extras: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("CAUSE:"):
            extras.append(stripped[len("CAUSE:") :].strip())
        elif stripped:
            narrative_lines.append(stripped)
    return " ".join(narrative_lines).strip(), extras
