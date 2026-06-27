"""REST endpoints for plugin discovery and lifecycle."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..analysis import AnalysisEngine
from ..plugins.metadata import PluginMetadata
from .deps import get_engine
from .schemas import PluginSummary, PluginToggleBody, PluginToggleResponse

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("", response_model=list[PluginSummary])
def list_plugins(engine: AnalysisEngine = Depends(get_engine)) -> list[PluginSummary]:
    """List all discovered plugins and their status."""
    return [
        PluginSummary(
            name=lp.plugin.metadata().name,
            version=lp.plugin.metadata().version,
            source=lp.source,
            enabled=lp.enabled,
            technologies=[str(t) for t in lp.plugin.metadata().supported_technologies],
        )
        for lp in engine.plugins.all_plugins()
    ]


@router.get("/{name}", response_model=PluginMetadata)
def get_plugin(name: str, engine: AnalysisEngine = Depends(get_engine)) -> PluginMetadata:
    """Return full metadata for a single plugin."""
    plugin = engine.plugins.get(name)
    if plugin is None:
        raise HTTPException(status_code=404, detail=f"Unknown plugin: {name}")
    return plugin.metadata()


@router.post("/enable", response_model=PluginToggleResponse)
def enable_plugin(
    body: PluginToggleBody, engine: AnalysisEngine = Depends(get_engine)
) -> PluginToggleResponse:
    """Enable a plugin for this server process."""
    if not engine.plugins.enable(body.name):
        raise HTTPException(status_code=404, detail=f"Unknown plugin: {body.name}")
    return PluginToggleResponse(name=body.name, enabled=True)


@router.post("/disable", response_model=PluginToggleResponse)
def disable_plugin(
    body: PluginToggleBody, engine: AnalysisEngine = Depends(get_engine)
) -> PluginToggleResponse:
    """Disable a plugin for this server process."""
    if not engine.plugins.disable(body.name):
        raise HTTPException(status_code=404, detail=f"Unknown plugin: {body.name}")
    return PluginToggleResponse(name=body.name, enabled=False)
