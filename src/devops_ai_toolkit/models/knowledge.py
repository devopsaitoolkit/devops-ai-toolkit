"""Models for the knowledge base of error signatures.

A *signature* is a declarative rule: a set of text patterns that, when matched
against an input, yields ranked root causes, read-only diagnostic commands,
suggested fixes, references and prevention advice. Signatures live as YAML data
files under ``knowledge/data`` so contributors can add coverage without touching
engine code.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

from .analysis import DiagnosticCommand, Reference, SuggestedFix, Warning
from .enums import SourceKind, Technology


class MatchSpec(BaseModel):
    """How a signature decides whether it applies to an input.

    - ``any_of``: signature fires if *any* pattern matches (logical OR).
    - ``all_of``: every pattern here must also match (logical AND), used to
      disambiguate look-alike errors.
    - patterns are case-insensitive regular expressions.
    """

    any_of: list[str] = Field(default_factory=list)
    all_of: list[str] = Field(default_factory=list)
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Base confidence when matched.")

    @field_validator("any_of", "all_of")
    @classmethod
    def _validate_regex(cls, patterns: list[str]) -> list[str]:
        for pattern in patterns:
            try:
                re.compile(pattern)
            except re.error as exc:  # pragma: no cover - guards malformed data files
                raise ValueError(f"invalid regex {pattern!r}: {exc}") from exc
        return patterns

    def evaluate(self, text: str) -> tuple[bool, list[str]]:
        """Return ``(matched, evidence)`` for ``text``.

        ``evidence`` is the list of matched line snippets, used to justify the
        finding to the operator.
        """
        flags = re.IGNORECASE | re.MULTILINE
        evidence: list[str] = []

        for pattern in self.all_of:
            match = re.search(pattern, text, flags)
            if not match:
                return False, []
            evidence.append(_snippet(text, match))

        any_ok = not self.any_of
        for pattern in self.any_of:
            match = re.search(pattern, text, flags)
            if match:
                any_ok = True
                evidence.append(_snippet(text, match))

        return any_ok, evidence


def _snippet(text: str, match: re.Match[str]) -> str:
    """Return the trimmed source line containing ``match``."""
    start = text.rfind("\n", 0, match.start()) + 1
    end = text.find("\n", match.end())
    if end == -1:
        end = len(text)
    return text[start:end].strip()[:200]


class CauseTemplate(BaseModel):
    """A candidate root cause defined in a signature."""

    title: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    category: str = "general"


class Signature(BaseModel):
    """A declarative troubleshooting rule for one error pattern."""

    id: str = Field(description="Stable unique id, e.g. 'k8s.crashloopbackoff'.")
    technology: Technology
    title: str
    summary: str
    applies_to: list[SourceKind] = Field(default_factory=lambda: [SourceKind.LOG])
    match: MatchSpec
    root_causes: list[CauseTemplate] = Field(default_factory=list)
    diagnostic_commands: list[DiagnosticCommand] = Field(default_factory=list)
    suggested_fixes: list[SuggestedFix] = Field(default_factory=list)
    references: list[Reference] = Field(default_factory=list)
    warnings: list[Warning] = Field(default_factory=list)
    best_practices: list[str] = Field(default_factory=list)
    prevention: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class SignatureMatch(BaseModel):
    """The result of a signature firing against an input."""

    signature: Signature
    score: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
