"""A reusable plugin base backed by knowledge-base signatures.

Most plugins — including all built-ins — are *data-driven*: they own a set of
:class:`Signature` rules plus an optional manifest validator. This base turns
that data into a complete :class:`AnalyzerPlugin`, so a concrete plugin is just
metadata + signatures + (optionally) a validator function. That keeps the path
to "hundreds of plugins" cheap while remaining a real, independent plugin.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from ..analysis.assembly import assemble_result, merge_validation
from ..detectors.matcher import SignatureMatcher
from ..knowledge.loader import KnowledgeBase
from ..models.analysis import AnalysisResult, ExplainResult, RootCause, ValidationResult
from ..models.enums import SourceKind, Technology
from ..models.knowledge import Signature
from ..utils.text import detect_source_kind, detect_technology
from ..validators.yaml_validator import validate_yaml
from .base import AnalyzerPlugin
from .metadata import PluginMetadata

Validator = Callable[[str], ValidationResult]

_WARNING_RE = re.compile(r"^.*\b(warn(?:ing)?|deprecat\w*)\b.*$", re.IGNORECASE | re.MULTILINE)
_RESOURCE_RES = [
    re.compile(r'resource\s+"([^"]+)"\s+"([^"]+)"'),  # terraform
    re.compile(r"\bpod[/\s]+([a-z0-9][a-z0-9.-]+)", re.IGNORECASE),  # k8s pods
    re.compile(r"\b(?:instance|server|volume|container)\s+([a-z0-9][\w.-]+)", re.IGNORECASE),
    re.compile(r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b"),  # uuids
]


class KnowledgeBackedPlugin(AnalyzerPlugin):
    """Concrete plugin built from signatures and an optional validator."""

    def __init__(
        self,
        metadata: PluginMetadata,
        signatures: list[Signature],
        validator: Validator | None = None,
    ) -> None:
        """Build the plugin's private matcher over its own signatures."""
        self._metadata = metadata
        self._signatures = signatures
        self._validator = validator
        self._kb = KnowledgeBase(signatures)
        self._matcher = SignatureMatcher(self._kb)

    def metadata(self) -> PluginMetadata:
        """Return this plugin's metadata."""
        return self._metadata

    def signatures(self) -> list[Signature]:
        """Return the signatures owned by this plugin."""
        return list(self._signatures)

    def supports(
        self,
        content: str,
        *,
        technology: Technology | None = None,
        source_kind: SourceKind | None = None,
        filename: str | None = None,
    ) -> bool:
        """True when the input matches this plugin's technology, file type, or signatures."""
        techs = set(self._metadata.supported_technologies)
        if technology is not None and technology in techs:
            return True
        if filename:
            lower = filename.lower()
            if any(lower.endswith(ext) for ext in self._metadata.supported_file_types):
                return True
        detected = technology or detect_technology(content, filename)
        if detected in techs:
            return True
        return bool(self._matcher.match(content, None, limit=1))

    def analyze(
        self,
        content: str,
        *,
        technology: Technology | None = None,
        source_kind: SourceKind | None = None,
        filename: str | None = None,
        max_root_causes: int = 5,
    ) -> AnalysisResult:
        """Match this plugin's signatures and assemble a result."""
        tech = technology or detect_technology(content, filename)
        kind = source_kind or detect_source_kind(content, filename)
        if tech is Technology.UNKNOWN and self._metadata.supported_technologies:
            tech = self._metadata.supported_technologies[0]
        matches = self._matcher.match(content, None)
        result = assemble_result(
            matches=matches,
            technology=tech,
            source_kind=kind,
            max_root_causes=max_root_causes,
            signatures_evaluated=len(self._kb),
            engine_label=f"plugin:{self._metadata.name}",
        )
        if self._validator is not None and kind in (
            SourceKind.YAML,
            SourceKind.KUBERNETES_MANIFEST,
            SourceKind.TERRAFORM,
            SourceKind.COMPOSE,
        ):
            merge_validation(result, self._validator(content))
        return result

    def validate(self, content: str, *, filename: str | None = None) -> ValidationResult:
        """Validate using the plugin's validator, or generic YAML as a fallback."""
        if self._validator is not None:
            return self._validator(content)
        return validate_yaml(content)

    def explain(self, query: str) -> ExplainResult | None:
        """Explain a named error from this plugin's signatures, or None."""
        signature = self._kb.get(query.strip())
        if signature is None:
            hits = self._kb.search(query)
            signature = hits[0] if hits else None
        if signature is None:
            return None
        return ExplainResult(
            query=query,
            technology=signature.technology,
            title=signature.title,
            summary=signature.summary,
            root_causes=[
                RootCause(
                    title=c.title,
                    description=c.description,
                    confidence=c.confidence,
                    category=c.category,
                )
                for c in signature.root_causes
            ],
            diagnostic_commands=list(signature.diagnostic_commands),
            suggested_fixes=list(signature.suggested_fixes),
            references=list(signature.references),
            best_practices=list(signature.best_practices),
        )

    def extract_errors(self, content: str) -> list[str]:
        """Return the evidence lines that matched this plugin's signatures."""
        seen: set[str] = set()
        out: list[str] = []
        for match in self._matcher.match(content, None):
            for line in match.evidence:
                if line and line not in seen:
                    seen.add(line)
                    out.append(line)
        return out

    def extract_warnings(self, content: str) -> list[str]:
        """Return lines that look like warnings or deprecations."""
        return [m.group(0).strip()[:200] for m in _WARNING_RE.finditer(content)]

    def extract_resources(self, content: str) -> list[str]:
        """Return resource identifiers referenced in ``content``."""
        found: list[str] = []
        seen: set[str] = set()
        for pattern in _RESOURCE_RES:
            for match in pattern.finditer(content):
                token = ".".join(g for g in match.groups() if g) or match.group(0)
                if token not in seen:
                    seen.add(token)
                    found.append(token)
        return found[:50]

    def extract_recommendations(self, result: AnalysisResult) -> list[str]:
        """Return actionable recommendations from a result."""
        recs = list(result.best_practices)
        recs.extend(result.prevention)
        recs.extend(f"Fix: {fix.title}" for fix in result.suggested_fixes)
        seen: set[str] = set()
        out: list[str] = []
        for rec in recs:
            if rec not in seen:
                seen.add(rec)
                out.append(rec)
        return out
