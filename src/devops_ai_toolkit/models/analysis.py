"""Pydantic models describing analysis inputs and outputs.

The :class:`AnalysisResult` is the single contract returned by the engine and
serialized by every interface (CLI renders it with Rich, the REST API returns it
as JSON, the SDK hands it back to callers). Keep it stable and additive.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, computed_field

from .enums import ConfidenceBand, Severity, SourceKind, Technology


class Reference(BaseModel):
    """A documentation pointer supporting a finding."""

    title: str
    url: str
    source: str = Field(
        default="", description="Where the reference comes from, e.g. 'official docs'."
    )


class DiagnosticCommand(BaseModel):
    """A READ-ONLY command a human can run to confirm a hypothesis.

    The toolkit never executes these; it only suggests and explains them.
    """

    command: str
    explanation: str = Field(description="Why this command helps and what it inspects.")
    expected_output: str = Field(
        default="",
        description="What a healthy or revealing result looks like.",
    )
    platform: str = Field(default="", description="Where to run it, e.g. 'control plane node'.")
    read_only: bool = Field(
        default=True,
        description="Always true. The toolkit only ever suggests non-mutating commands.",
    )


class SuggestedFix(BaseModel):
    """A remediation suggestion. Described as guidance, never auto-applied."""

    title: str
    description: str
    snippet: str = Field(
        default="", description="Optional config/code snippet illustrating the fix."
    )
    references: list[Reference] = Field(default_factory=list)


class RootCause(BaseModel):
    """A ranked candidate explanation for the observed symptoms."""

    title: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0, description="0.0-1.0 likelihood this is the cause.")
    category: str = Field(default="general")
    evidence: list[str] = Field(
        default_factory=list,
        description="Snippets from the input that support this cause.",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def confidence_percent(self) -> int:
        """Confidence expressed as a whole percentage."""
        return round(self.confidence * 100)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def confidence_band(self) -> ConfidenceBand:
        """Human-friendly confidence bucket."""
        return ConfidenceBand.from_score(self.confidence)


class Warning(BaseModel):
    """A caution surfaced to the operator (e.g. data-loss risk in a fix)."""

    message: str
    severity: Severity = Severity.MEDIUM


class AnalysisRequest(BaseModel):
    """Input to the engine. Used by the SDK and REST API."""

    content: str = Field(description="Raw text to analyze: a log, manifest, or command output.")
    technology: Technology | None = Field(
        default=None,
        description="Optional hint. If omitted the engine auto-detects.",
    )
    source_kind: SourceKind | None = Field(
        default=None,
        description="Optional hint about the input shape. Auto-detected when omitted.",
    )
    filename: str | None = Field(
        default=None, description="Optional original filename, aids detection."
    )
    enrich: bool = Field(
        default=False,
        description="If true and an AI provider is configured, add LLM-generated narrative.",
    )
    max_root_causes: int = Field(default=5, ge=1, le=20)


class Enrichment(BaseModel):
    """Optional LLM-generated narrative layered on top of deterministic findings."""

    provider: str
    model: str
    narrative: str
    additional_causes: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    """The canonical, interface-agnostic output of an analysis."""

    summary: str
    technology: Technology
    source_kind: SourceKind
    signatures_matched: list[str] = Field(
        default_factory=list,
        description="IDs of knowledge-base signatures that fired.",
    )
    root_causes: list[RootCause] = Field(default_factory=list)
    diagnostic_commands: list[DiagnosticCommand] = Field(default_factory=list)
    suggested_fixes: list[SuggestedFix] = Field(default_factory=list)
    references: list[Reference] = Field(default_factory=list)
    warnings: list[Warning] = Field(default_factory=list)
    best_practices: list[str] = Field(default_factory=list)
    prevention: list[str] = Field(default_factory=list)
    enrichment: Enrichment | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def confidence(self) -> float:
        """Overall confidence — the strongest single root cause, 0.0 if none."""
        if not self.root_causes:
            return 0.0
        return max(rc.confidence for rc in self.root_causes)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def confidence_percent(self) -> int:
        """Overall confidence as a whole percentage."""
        return round(self.confidence * 100)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def matched(self) -> bool:
        """True if at least one signature/root cause was found."""
        return bool(self.root_causes)


class ExplainResult(BaseModel):
    """Output of an 'explain this error' lookup."""

    query: str
    technology: Technology
    title: str
    summary: str
    root_causes: list[RootCause] = Field(default_factory=list)
    diagnostic_commands: list[DiagnosticCommand] = Field(default_factory=list)
    suggested_fixes: list[SuggestedFix] = Field(default_factory=list)
    references: list[Reference] = Field(default_factory=list)
    best_practices: list[str] = Field(default_factory=list)
    matched: bool = True


class ValidationIssue(BaseModel):
    """A single problem found while validating a manifest."""

    severity: Severity
    message: str
    line: int | None = None
    path: str = Field(default="", description="Dotted path to the offending field, when known.")
    hint: str = ""


class ValidationResult(BaseModel):
    """Output of validating a YAML / Kubernetes / Terraform document."""

    technology: Technology
    source_kind: SourceKind
    valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
    best_practices: list[str] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def error_count(self) -> int:
        """Number of error/critical severity issues."""
        return sum(1 for i in self.issues if i.severity in (Severity.HIGH, Severity.CRITICAL))
