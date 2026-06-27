"""Generic YAML syntax validation."""

from __future__ import annotations

from ..models.analysis import ValidationIssue, ValidationResult
from ..models.enums import Severity, SourceKind, Technology
from ..parsers.yaml_docs import parse_yaml_documents


def validate_yaml(text: str) -> ValidationResult:
    """Validate that ``text`` is well-formed YAML.

    Returns a structured result with line-located syntax errors. This never
    executes or renders the document — it only parses it.
    """
    parsed = parse_yaml_documents(text)
    issues: list[ValidationIssue] = []
    if not parsed.ok:
        issues.append(
            ValidationIssue(
                severity=Severity.HIGH,
                message=parsed.error or "Invalid YAML.",
                line=parsed.error_line,
                hint="Check indentation, tabs vs spaces, and unbalanced quotes/brackets.",
            )
        )
    return ValidationResult(
        technology=Technology.UNKNOWN,
        source_kind=SourceKind.YAML,
        valid=parsed.ok,
        issues=issues,
        best_practices=[
            "Use 2-space indentation and never tabs in YAML.",
            "Validate manifests in CI before they reach a cluster or pipeline.",
        ],
    )
