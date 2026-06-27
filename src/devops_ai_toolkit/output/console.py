"""Rich terminal rendering for analysis, explanation and validation results.

Renders the canonical output sections: Summary, Likely Causes (+ confidence),
Diagnostic Commands (+ explanation + expected output), Suggested Fixes,
References, Warnings, Best Practices and Prevention.
"""

from __future__ import annotations

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..models.analysis import AnalysisResult, ExplainResult, ValidationResult
from ..models.enums import ConfidenceBand, Severity

_BAND_STYLE = {
    ConfidenceBand.VERY_HIGH: "bold green",
    ConfidenceBand.HIGH: "green",
    ConfidenceBand.MODERATE: "yellow",
    ConfidenceBand.LOW: "orange3",
    ConfidenceBand.VERY_LOW: "red",
}
_SEVERITY_STYLE = {
    Severity.CRITICAL: "bold red",
    Severity.HIGH: "red",
    Severity.MEDIUM: "yellow",
    Severity.LOW: "cyan",
    Severity.INFO: "dim",
}


def _bar(percent: int) -> Text:
    """A small unicode confidence bar."""
    filled = round(percent / 10)
    band = ConfidenceBand.from_score(percent / 100)
    style = _BAND_STYLE[band]
    return Text("█" * filled + "░" * (10 - filled) + f" {percent}%", style=style)


def render_analysis(result: AnalysisResult, console: Console | None = None) -> None:
    """Render a full :class:`AnalysisResult` to the terminal."""
    console = console or Console()
    header = Text(f"  {result.technology} · {result.source_kind}", style="bold cyan")
    console.print(
        Panel(Text(result.summary), title="Summary", border_style="cyan", subtitle=str(header))
    )

    if result.root_causes:
        table = Table(title="Likely Causes", expand=True, header_style="bold")
        table.add_column("#", width=3)
        table.add_column("Root Cause")
        table.add_column("Confidence", width=18)
        for i, rc in enumerate(result.root_causes, 1):
            table.add_row(
                str(i),
                Text.assemble((rc.title, "bold"), "\n", (rc.description, "dim")),
                _bar(rc.confidence_percent),
            )
        console.print(table)

    for cmd in result.diagnostic_commands:
        body = Group(
            Text(cmd.command, style="bold white on grey15"),
            Text(f"\n{cmd.explanation}", style="default"),
            Text(f"\nExpected: {cmd.expected_output}", style="green")
            if cmd.expected_output
            else Text(""),
        )
        console.print(
            Panel(
                body,
                title=f"🔎 Diagnostic{f' · {cmd.platform}' if cmd.platform else ''}",
                border_style="blue",
            )
        )

    if result.suggested_fixes:
        items = [
            Text.assemble(("• ", "green"), (f.title, "bold"), (f" — {f.description}", "default"))
            for f in result.suggested_fixes
        ]
        console.print(
            Panel(
                Group(*items),
                title="🛠  Suggested Fixes (review before applying)",
                border_style="green",
            )
        )

    _render_lists(
        console, result.warnings, result.best_practices, result.prevention, result.references
    )

    if result.enrichment:
        console.print(
            Panel(
                Text(result.enrichment.narrative),
                title=f"🤖 AI Insight · {result.enrichment.provider}/{result.enrichment.model}",
                border_style="magenta",
            )
        )


def _render_lists(console: Console, warnings, best_practices, prevention, references) -> None:  # type: ignore[no-untyped-def]
    """Render the warning/best-practice/prevention/reference sections."""
    if warnings:
        lines = [
            Text.assemble(
                (f"[{w.severity}] ", _SEVERITY_STYLE.get(w.severity, "yellow")), w.message
            )
            for w in warnings
        ]
        console.print(Panel(Group(*lines), title="⚠  Warnings", border_style="yellow"))
    if best_practices:
        console.print(
            Panel(
                Group(*[Text(f"• {b}") for b in best_practices]),
                title="✅ Best Practices",
                border_style="green",
            )
        )
    if prevention:
        console.print(
            Panel(
                Group(*[Text(f"• {p}") for p in prevention]),
                title="🛡  Prevention",
                border_style="cyan",
            )
        )
    if references:
        console.print(
            Panel(
                Group(
                    *[
                        Text.assemble(
                            ("• ", "blue"), (r.title, "bold"), (f"\n  {r.url}", "blue underline")
                        )
                        for r in references
                    ]
                ),
                title="📚 References",
                border_style="blue",
            )
        )


def render_explanation(result: ExplainResult, console: Console | None = None) -> None:
    """Render an :class:`ExplainResult` to the terminal."""
    console = console or Console()
    console.print(
        Panel(
            Text.assemble((result.title + "\n", "bold"), (result.summary, "default")),
            title=f"{result.technology} · {result.query}",
            border_style="cyan",
        )
    )
    if result.root_causes:
        table = Table(title="Likely Causes", expand=True)
        table.add_column("Root Cause")
        table.add_column("Confidence", width=18)
        for rc in result.root_causes:
            table.add_row(
                Text.assemble((rc.title, "bold"), "\n", (rc.description, "dim")),
                _bar(rc.confidence_percent),
            )
        console.print(table)
    for cmd in result.diagnostic_commands:
        console.print(
            Panel(
                Group(
                    Text(cmd.command, style="bold white on grey15"), Text(f"\n{cmd.explanation}")
                ),
                title="🔎 Diagnostic",
                border_style="blue",
            )
        )
    _render_lists(console, [], result.best_practices, [], result.references)


def render_validation(result: ValidationResult, console: Console | None = None) -> None:
    """Render a :class:`ValidationResult` to the terminal."""
    console = console or Console()
    status = (
        Text("VALID", style="bold green")
        if result.valid
        else Text("ISSUES FOUND", style="bold red")
    )
    console.print(
        Panel(
            status,
            title=f"Validation · {result.technology}",
            border_style="green" if result.valid else "red",
        )
    )
    if result.issues:
        table = Table(expand=True)
        table.add_column("Severity", width=10)
        table.add_column("Line", width=6)
        table.add_column("Message")
        for issue in result.issues:
            table.add_row(
                Text(str(issue.severity), style=_SEVERITY_STYLE.get(issue.severity, "white")),
                str(issue.line or "-"),
                Text.assemble(
                    (issue.message, "default"),
                    (f"\n{issue.hint}", "dim") if issue.hint else ("", ""),
                ),
            )
        console.print(table)
    if result.best_practices:
        console.print(
            Panel(
                Group(*[Text(f"• {b}") for b in result.best_practices]),
                title="✅ Best Practices",
                border_style="green",
            )
        )
