"""Pure functions that assemble an :class:`AnalysisResult` from signature matches.

Extracted from the engine so the engine **and** every plugin build results the
same way — there is exactly one place that turns matches into a result.
"""

from __future__ import annotations

from ..models.analysis import (
    AnalysisResult,
    DiagnosticCommand,
    Reference,
    RootCause,
    ValidationResult,
    Warning,
)
from ..models.enums import SourceKind, Technology
from ..models.knowledge import SignatureMatch


def assemble_result(
    *,
    matches: list[SignatureMatch],
    technology: Technology,
    source_kind: SourceKind,
    max_root_causes: int,
    signatures_evaluated: int,
    engine_label: str = "deterministic",
) -> AnalysisResult:
    """Build an :class:`AnalysisResult` from ranked signature matches."""
    root_causes: list[RootCause] = []
    diagnostic_commands: list[DiagnosticCommand] = []
    suggested_fixes = []
    references: list[Reference] = []
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
    root_causes = root_causes[:max_root_causes]

    return AnalysisResult(
        summary=summarise(technology, root_causes),
        technology=technology,
        source_kind=source_kind,
        signatures_matched=matched_ids,
        root_causes=root_causes,
        diagnostic_commands=dedupe_commands(diagnostic_commands),
        suggested_fixes=suggested_fixes,
        references=dedupe_references(references),
        warnings=warnings,
        best_practices=dedupe_str(best_practices),
        prevention=dedupe_str(prevention),
        metadata={
            "engine": engine_label,
            "signatures_evaluated": str(signatures_evaluated),
        },
    )


def summarise(technology: Technology, root_causes: list[RootCause]) -> str:
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


def dedupe_commands(commands: list[DiagnosticCommand]) -> list[DiagnosticCommand]:
    """Remove duplicate diagnostic commands, preserving order."""
    seen: set[str] = set()
    out: list[DiagnosticCommand] = []
    for cmd in commands:
        if cmd.command not in seen:
            seen.add(cmd.command)
            out.append(cmd)
    return out


def dedupe_references(references: list[Reference]) -> list[Reference]:
    """Remove duplicate references by URL, preserving order."""
    seen: set[str] = set()
    out: list[Reference] = []
    for ref in references:
        if ref.url not in seen:
            seen.add(ref.url)
            out.append(ref)
    return out


def dedupe_str(items: list[str]) -> list[str]:
    """Remove duplicate strings, preserving order."""
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def merge_validation(result: AnalysisResult, validation: ValidationResult) -> None:
    """Fold validator issues and best-practices into an analysis result in place."""
    for issue in validation.issues:
        result.warnings.append(
            Warning(
                message=f"{issue.message} {issue.hint}".strip()
                + (f" ({issue.path})" if issue.path else ""),
                severity=issue.severity,
            )
        )
    for tip in validation.best_practices:
        if tip not in result.best_practices:
            result.best_practices.append(tip)
