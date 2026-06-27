"""The :class:`AnalysisEngine` — every interface calls this and nothing else.

Business logic lives here and only here. The CLI, SDK and REST API are thin
adapters over this engine, guaranteeing identical behaviour everywhere.

The engine is **read-only**: it inspects text and emits guidance. It never
executes commands, mutates files, or touches infrastructure.
"""

from __future__ import annotations

from pathlib import Path

from ..analyzers.registry import get_analyzer
from ..detectors.matcher import SignatureMatcher
from ..knowledge.loader import KnowledgeBase, load_default_knowledge_base
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
from ..models.knowledge import Signature, SignatureMatch
from ..prompts.enrichment import ENRICHMENT_SYSTEM_PROMPT, build_enrichment_prompt
from ..providers.base import AIProvider, CompletionRequest, NullProvider
from ..providers.registry import get_provider
from ..utils.config import Settings, get_settings
from ..utils.logging import get_logger
from ..utils.text import detect_source_kind, detect_technology, truncate
from ..validators.service import validate_manifest

_logger = get_logger(__name__)


class AnalysisEngine:
    """Stateless, dependency-injected façade over the analysis pipeline.

    Args:
        knowledge_base: Signatures to match against. Defaults to the packaged base.
        provider: AI provider for optional enrichment. Defaults to the configured
            one (offline ``NullProvider`` when nothing is set up).
        settings: Resolved runtime settings. Defaults to environment-derived.
    """

    def __init__(
        self,
        knowledge_base: KnowledgeBase | None = None,
        provider: AIProvider | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Wire the engine's collaborators, all overridable for testing."""
        self.settings = settings or get_settings()
        self.knowledge_base = knowledge_base or load_default_knowledge_base()
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
        result = self._build_result(content, technology, source_kind, matches, request)

        analyzer = get_analyzer(source_kind, technology)
        if analyzer is not None:
            result = analyzer.augment(result, content)

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
        """Validate a manifest (YAML / Kubernetes / Terraform). Read-only."""
        return validate_manifest(
            content, technology=technology, source_kind=source_kind, filename=filename
        )

    # ------------------------------------------------------------------ #
    # Internals                                                          #
    # ------------------------------------------------------------------ #

    def _build_result(
        self,
        content: str,
        technology: Technology,
        source_kind: SourceKind,
        matches: list[SignatureMatch],
        request: AnalysisRequest,
    ) -> AnalysisResult:
        """Assemble an :class:`AnalysisResult` from ranked signature matches."""
        root_causes: list[RootCause] = []
        diagnostic_commands = []
        suggested_fixes = []
        references = []
        warnings = []
        best_practices: list[str] = []
        prevention: list[str] = []
        matched_ids: list[str] = []

        for match in matches:
            sig = match.signature
            matched_ids.append(sig.id)
            for cause in sig.root_causes:
                # Blend the signature's match score with the cause's own prior.
                blended = round(min(0.5 * match.score + 0.5 * cause.confidence, 1.0), 4)
                root_causes.append(
                    RootCause(
                        title=cause.title,
                        description=cause.description,
                        confidence=blended,
                        category=cause.category,
                        evidence=match.evidence,
                    )
                )
            diagnostic_commands.extend(sig.diagnostic_commands)
            suggested_fixes.extend(sig.suggested_fixes)
            references.extend(sig.references)
            warnings.extend(sig.warnings)
            best_practices.extend(sig.best_practices)
            prevention.extend(sig.prevention)

        root_causes.sort(key=lambda rc: rc.confidence, reverse=True)
        root_causes = root_causes[: request.max_root_causes]

        summary = self._summarise(technology, root_causes)
        return AnalysisResult(
            summary=summary,
            technology=technology,
            source_kind=source_kind,
            signatures_matched=matched_ids,
            root_causes=root_causes,
            diagnostic_commands=_dedupe_commands(diagnostic_commands),
            suggested_fixes=suggested_fixes,
            references=_dedupe_references(references),
            warnings=warnings,
            best_practices=_dedupe_str(best_practices),
            prevention=_dedupe_str(prevention),
            metadata={
                "engine": "deterministic",
                "signatures_evaluated": str(len(self.knowledge_base)),
            },
        )

    @staticmethod
    def _summarise(technology: Technology, root_causes: list[RootCause]) -> str:
        """Produce a one-line human summary of the analysis."""
        if not root_causes:
            return (
                f"No known {technology} error signature matched. The input was read but "
                "did not match a catalogued pattern. Review it manually or enable AI enrichment."
            )
        top = root_causes[0]
        return (
            f"Most likely cause ({top.confidence_percent}% confidence): {top.title}. "
            f"{len(root_causes)} candidate cause(s) identified for {technology}."
        )

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


def _dedupe_commands(commands: list) -> list:  # type: ignore[type-arg]
    """Remove duplicate diagnostic commands, preserving order."""
    seen: set[str] = set()
    out = []
    for cmd in commands:
        if cmd.command not in seen:
            seen.add(cmd.command)
            out.append(cmd)
    return out


def _dedupe_references(references: list) -> list:  # type: ignore[type-arg]
    """Remove duplicate references by URL, preserving order."""
    seen: set[str] = set()
    out = []
    for ref in references:
        if ref.url not in seen:
            seen.add(ref.url)
            out.append(ref)
    return out


def _dedupe_str(items: list[str]) -> list[str]:
    """Remove duplicate strings, preserving order."""
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
