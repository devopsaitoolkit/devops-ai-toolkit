"""Structural checks for Terraform configurations (read-only)."""

from __future__ import annotations

from ..models.analysis import ValidationIssue, ValidationResult
from ..models.enums import Severity, SourceKind, Technology
from ..parsers.terraform import parse_terraform


def validate_terraform(text: str) -> ValidationResult:
    """Validate Terraform for balance issues and basic structure.

    This is a static, read-only review — it never runs ``terraform`` or touches
    state. It flags unbalanced braces/quotes and an absence of declared blocks.
    """
    parsed = parse_terraform(text)
    issues: list[ValidationIssue] = []

    if not parsed.brace_balanced:
        issues.append(
            ValidationIssue(
                severity=Severity.HIGH,
                message="Unbalanced braces '{' / '}' detected.",
                hint="Every block must be closed. Run `terraform fmt` to localise the error.",
            )
        )
    if not parsed.quote_balanced:
        issues.append(
            ValidationIssue(
                severity=Severity.HIGH,
                message="Unbalanced double quotes detected.",
                hint="A string literal is likely missing a closing quote.",
            )
        )
    if not parsed.blocks:
        issues.append(
            ValidationIssue(
                severity=Severity.LOW,
                message="No Terraform blocks (resource/module/provider/...) found.",
                hint="Confirm this is a .tf file and not a tfvars or plan output.",
            )
        )

    valid = not any(i.severity in (Severity.HIGH, Severity.CRITICAL) for i in issues)
    return ValidationResult(
        technology=Technology.TERRAFORM,
        source_kind=SourceKind.TERRAFORM,
        valid=valid,
        issues=issues,
        best_practices=[
            "Run `terraform validate` and `terraform fmt -check` in CI.",
            "Pin provider versions in required_providers.",
            "Review `terraform plan` output before every apply.",
        ],
    )
