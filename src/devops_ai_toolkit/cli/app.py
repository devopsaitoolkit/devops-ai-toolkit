"""The ``devops-ai`` command line application.

A thin Typer wrapper over :class:`~devops_ai_toolkit.analysis.engine.AnalysisEngine`.
All real work happens in the engine; this module only handles I/O and rendering.
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console

from .._version import __version__
from ..analysis import AnalysisEngine
from ..explainers import ErrorCatalog
from ..models.enums import Technology
from ..output import render_analysis, render_explanation, render_validation, to_json
from .plugins import build_manager, plugins_app
from .scaffold import create_plugin as scaffold_plugin

app = typer.Typer(
    name="devops-ai",
    help="AI-powered, read-only DevOps troubleshooting for logs, YAML, Terraform & more.",
    add_completion=True,
    no_args_is_help=True,
    rich_markup_mode="rich",
)
app.add_typer(plugins_app, name="plugins")
console = Console()
err_console = Console(stderr=True)


def _read_input(source: str | None) -> tuple[str, str | None]:
    """Return ``(content, filename)`` from a path argument or stdin (``-``)."""
    if source is None or source == "-":
        if sys.stdin.isatty():
            err_console.print("[red]No input. Pass a file path or pipe content via stdin.[/red]")
            raise typer.Exit(code=2)
        return sys.stdin.read(), None
    path = Path(source)
    if not path.exists():
        err_console.print(f"[red]File not found:[/red] {source}")
        raise typer.Exit(code=2)
    return path.read_text(encoding="utf-8", errors="replace"), path.name


def _engine(provider: str | None) -> AnalysisEngine:
    """Construct an engine that respects disabled plugins, optional provider override."""
    manager = build_manager()
    if provider:
        from ..providers.registry import get_provider

        return AnalysisEngine(provider=get_provider(provider), plugin_manager=manager)
    return AnalysisEngine(plugin_manager=manager)


@app.command()
def analyze(
    source: str | None = typer.Argument(None, help="File to analyze, or '-' for stdin."),
    technology: str | None = typer.Option(None, "--tech", "-t", help="Technology hint."),
    enrich: bool = typer.Option(False, "--enrich", help="Add LLM narrative (needs a provider)."),
    provider: str | None = typer.Option(None, "--provider", help="anthropic|openai|gemini|ollama."),
    json_out: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Analyze a log, manifest, Terraform file or command output."""
    content, filename = _read_input(source)
    tech = Technology(technology) if technology else None
    result = _engine(provider).analyze_text(
        content, technology=tech, filename=filename, enrich=enrich
    )
    if json_out:
        console.print_json(to_json(result))
    else:
        render_analysis(result, console)
    raise typer.Exit(code=0 if result.matched else 1)


@app.command()
def explain(
    error: str = typer.Argument(..., help="Error name or message, e.g. 'CrashLoopBackOff'."),
    json_out: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Explain a known error from the knowledge base."""
    result = AnalysisEngine().explain_error(error)
    if json_out:
        console.print_json(to_json(result))
    else:
        render_explanation(result, console)
    raise typer.Exit(code=0 if result.matched else 1)


@app.command()
def validate(
    source: str | None = typer.Argument(None, help="Manifest/Terraform file, or '-' for stdin."),
    json_out: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Validate a YAML, Kubernetes or Terraform document (read-only)."""
    content, filename = _read_input(source)
    result = AnalysisEngine().validate_manifest(content, filename=filename)
    if json_out:
        console.print_json(to_json(result))
    else:
        render_validation(result, console)
    raise typer.Exit(code=0 if result.valid else 1)


@app.command(name="list")
def list_catalog(
    technology: str | None = typer.Option(None, "--tech", "-t", help="Filter by technology."),
) -> None:
    """List the error signatures the toolkit knows about."""
    from rich.table import Table

    catalog = ErrorCatalog()
    tech = Technology(technology) if technology else None
    table = Table(title=f"Knowledge Base · {len(catalog)} signatures")
    table.add_column("ID", style="cyan")
    table.add_column("Technology")
    table.add_column("Title")
    for entry in catalog.entries(tech):
        table.add_row(entry.id, str(entry.technology), entry.title)
    console.print(table)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Bind host."),
    port: int = typer.Option(8000, help="Bind port."),
) -> None:
    """Run the FastAPI REST API (requires the 'api' extra)."""
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover - optional dependency
        err_console.print("[red]Install the API extra:[/red] pip install 'devops-ai-toolkit[api]'")
        raise typer.Exit(code=1) from exc
    uvicorn.run("devops_ai_toolkit.api.app:app", host=host, port=port, factory=False)


@app.command(name="create-plugin")
def create_plugin(
    name: str = typer.Argument(..., help="Plugin name, e.g. 'mycompany-plugin'."),
    directory: str = typer.Option(".", "--dir", "-d", help="Where to create the project."),
) -> None:
    """Scaffold a new, installable third-party plugin project."""
    path = scaffold_plugin(name, directory)
    console.print(f"[green]Created plugin project[/green] at [bold]{path}[/bold]")
    console.print(
        "\nNext steps:\n"
        f"  cd {path}\n"
        "  pip install -e .\n"
        "  devops-ai plugins list   [dim]# your plugin appears, auto-discovered[/dim]\n"
        "  edit the plugin module to add your error signatures, then publish.\n"
    )


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"devops-ai-toolkit [bold cyan]{__version__}[/bold cyan]")


def main() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
