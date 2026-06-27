"""The ``devops-ai plugins`` command group.

Lists, inspects and toggles plugins. Enable/disable state is persisted to a small
JSON file so the choice survives across invocations; the engine reads the same
state on startup.
"""

from __future__ import annotations

import json
import os
from importlib import metadata as importlib_metadata
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from ..plugins.manager import ENTRY_POINT_GROUP, PluginManager

plugins_app = typer.Typer(
    help="Discover, inspect and toggle analyzer plugins.", no_args_is_help=True
)
console = Console()


def _state_path() -> Path:
    """Return the path of the plugin enable/disable state file."""
    override = os.environ.get("DEVOPS_AI_STATE")
    if override:
        return Path(override).expanduser()
    base = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(base) / "devops-ai" / "plugins.json"


def _load_disabled() -> set[str]:
    """Load the set of disabled plugin names from the state file."""
    path = _state_path()
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return set(data.get("disabled", []))
    except (json.JSONDecodeError, OSError):
        return set()


def _save_disabled(disabled: set[str]) -> None:
    """Persist the set of disabled plugin names."""
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"disabled": sorted(disabled)}, indent=2), encoding="utf-8")


def build_manager() -> PluginManager:
    """Build a manager with persisted disable-state applied.

    Shared with the analyze/validate commands so a disabled plugin is actually
    skipped during analysis, not just hidden from ``plugins list``.
    """
    manager = PluginManager.create_default()
    for name in _load_disabled():
        manager.disable(name)
    return manager


# Backwards-friendly internal alias.
_manager = build_manager


@plugins_app.command("list")
def list_plugins() -> None:
    """List all discovered plugins and their status."""
    manager = _manager()
    table = Table(title=f"Plugins ({len(manager.all_plugins())})")
    table.add_column("Name", style="cyan")
    table.add_column("Version")
    table.add_column("Source")
    table.add_column("Status")
    table.add_column("Technologies")
    for loaded in manager.all_plugins():
        meta = loaded.plugin.metadata()
        status = "[green]enabled[/green]" if loaded.enabled else "[dim]disabled[/dim]"
        techs = ", ".join(str(t) for t in meta.supported_technologies)
        table.add_row(meta.name, meta.version, loaded.source, status, techs)
    console.print(table)
    failures = manager.failures()
    if failures:
        console.print(
            f"[yellow]{len(failures)} plugin(s) failed to load. Run 'plugins doctor'.[/yellow]"
        )


@plugins_app.command("info")
def info(name: str = typer.Argument(..., help="Plugin name.")) -> None:
    """Show detailed metadata for a plugin."""
    plugin = _manager().get(name)
    if plugin is None:
        console.print(f"[red]Unknown plugin:[/red] {name}")
        raise typer.Exit(code=1)
    meta = plugin.metadata()
    console.print_json(meta.model_dump_json(indent=2))


@plugins_app.command("enable")
def enable(name: str = typer.Argument(..., help="Plugin name.")) -> None:
    """Enable a plugin (persisted)."""
    if _manager().get(name) is None:
        console.print(f"[red]Unknown plugin:[/red] {name}")
        raise typer.Exit(code=1)
    disabled = _load_disabled()
    disabled.discard(name)
    _save_disabled(disabled)
    console.print(f"[green]Enabled[/green] {name}")


@plugins_app.command("disable")
def disable(name: str = typer.Argument(..., help="Plugin name.")) -> None:
    """Disable a plugin (persisted)."""
    if _manager().get(name) is None:
        console.print(f"[red]Unknown plugin:[/red] {name}")
        raise typer.Exit(code=1)
    disabled = _load_disabled()
    disabled.add(name)
    _save_disabled(disabled)
    console.print(f"[yellow]Disabled[/yellow] {name}")


@plugins_app.command("doctor")
def doctor() -> None:
    """Run a health check across discovered plugins."""
    report = _manager().doctor()
    console.print_json(json.dumps(report))
    if report["failures"]:
        raise typer.Exit(code=1)


@plugins_app.command("update")
def update() -> None:
    """Show how to update installed plugin packages."""
    console.print(
        "Plugins are distributed as Python packages. Update them with your "
        "package manager, e.g.:\n  [cyan]pip install -U <plugin-package>[/cyan]\n"
    )
    dists: set[str] = set()
    try:
        for ep in importlib_metadata.entry_points(group=ENTRY_POINT_GROUP):
            if ep.dist is not None:
                dists.add(f"{ep.dist.name}=={ep.dist.version}")
    except Exception:
        pass
    if dists:
        console.print("Installed plugin distributions:")
        for d in sorted(dists):
            console.print(f"  • {d}")
    else:
        console.print("[dim]No third-party plugin packages installed (built-ins only).[/dim]")
