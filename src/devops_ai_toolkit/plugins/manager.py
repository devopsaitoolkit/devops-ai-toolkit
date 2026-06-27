"""The Plugin Manager: discovery, lifecycle, health and aggregation.

Discovery has two independent sources, so the engine needs **no code changes**
when a plugin is installed:

1. Built-in plugins — every module under ``plugins.builtin`` exposing a
   module-level ``PLUGIN`` (an :class:`AnalyzerPlugin`).
2. Third-party plugins — any installed distribution advertising a
   ``devops_ai_toolkit.plugins`` entry point.

Each load is isolated: a broken plugin is recorded as a failure (surfaced by
``doctor``) and never crashes the manager or the engine.
"""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass, field
from importlib import metadata as importlib_metadata

from .._version import __version__
from ..knowledge.loader import KnowledgeBase
from ..models.enums import SourceKind, Technology
from ..models.knowledge import Signature
from ..utils.logging import get_logger
from .base import AnalyzerPlugin

_logger = get_logger(__name__)

ENTRY_POINT_GROUP = "devops_ai_toolkit.plugins"
_BUILTIN_PACKAGE = "devops_ai_toolkit.plugins.builtin"


@dataclass
class LoadedPlugin:
    """A successfully loaded plugin plus bookkeeping state."""

    plugin: AnalyzerPlugin
    source: str  # "builtin" or "entrypoint"
    enabled: bool = True


@dataclass
class PluginFailure:
    """Records a plugin that failed to load or was incompatible."""

    name: str
    source: str
    reason: str


@dataclass
class PluginManager:
    """Discovers, holds and routes to analyzer plugins."""

    core_version: str = __version__
    _plugins: dict[str, LoadedPlugin] = field(default_factory=dict)
    _failures: list[PluginFailure] = field(default_factory=list)
    _kb_cache: KnowledgeBase | None = field(default=None, repr=False)

    # ------------------------------------------------------------------ #
    # Construction / discovery                                           #
    # ------------------------------------------------------------------ #

    @classmethod
    def create_default(cls) -> PluginManager:
        """Build a manager with all discoverable plugins loaded."""
        manager = cls()
        manager.discover()
        return manager

    def discover(self) -> None:
        """Discover built-in and entry-point plugins (idempotent)."""
        self._discover_builtin()
        self._discover_entrypoints()
        self._kb_cache = None

    def _discover_builtin(self) -> None:
        try:
            package = importlib.import_module(_BUILTIN_PACKAGE)
        except ModuleNotFoundError:  # pragma: no cover - builtin pkg always present
            return
        for module_info in pkgutil.iter_modules(package.__path__):
            full_name = f"{_BUILTIN_PACKAGE}.{module_info.name}"
            try:
                module = importlib.import_module(full_name)
                plugin = getattr(module, "PLUGIN", None)
                if isinstance(plugin, AnalyzerPlugin):
                    self._register(plugin, source="builtin")
            except Exception as exc:
                self._failures.append(PluginFailure(module_info.name, "builtin", str(exc)))

    def _discover_entrypoints(self) -> None:
        try:
            entry_points = importlib_metadata.entry_points(group=ENTRY_POINT_GROUP)
        except TypeError:  # pragma: no cover - very old importlib.metadata
            entry_points = importlib_metadata.entry_points().get(ENTRY_POINT_GROUP, [])  # type: ignore[attr-defined]
        for entry_point in entry_points:
            try:
                loaded = entry_point.load()
                plugin = (
                    loaded()
                    if callable(loaded) and not isinstance(loaded, AnalyzerPlugin)
                    else loaded
                )
                if isinstance(plugin, AnalyzerPlugin):
                    self._register(plugin, source="entrypoint")
                else:
                    raise TypeError("entry point did not resolve to an AnalyzerPlugin")
            except Exception as exc:
                self._failures.append(PluginFailure(entry_point.name, "entrypoint", str(exc)))

    def _register(self, plugin: AnalyzerPlugin, *, source: str) -> None:
        meta = plugin.metadata()
        if not meta.is_compatible(self.core_version):
            self._failures.append(
                PluginFailure(
                    meta.name,
                    source,
                    f"requires core >= {meta.minimum_core_version}, have {self.core_version}",
                )
            )
            return
        if meta.name in self._plugins:
            # Conflict resolution: entry-point plugins may override built-ins.
            existing = self._plugins[meta.name]
            if existing.source == "builtin" and source == "entrypoint":
                _logger.warning("Plugin %r from %s overrides built-in.", meta.name, source)
            else:
                self._failures.append(
                    PluginFailure(meta.name, source, "duplicate plugin name; ignored")
                )
                return
        self._plugins[meta.name] = LoadedPlugin(plugin=plugin, source=source)
        self._kb_cache = None

    def register(self, plugin: AnalyzerPlugin, *, source: str = "manual") -> None:
        """Register a plugin instance directly (useful for tests/embedding)."""
        self._register(plugin, source=source)

    # ------------------------------------------------------------------ #
    # Lifecycle                                                          #
    # ------------------------------------------------------------------ #

    def enable(self, name: str) -> bool:
        """Enable a plugin by name. Returns False if unknown."""
        if name not in self._plugins:
            return False
        self._plugins[name].enabled = True
        self._kb_cache = None
        return True

    def disable(self, name: str) -> bool:
        """Disable a plugin by name. Returns False if unknown."""
        if name not in self._plugins:
            return False
        self._plugins[name].enabled = False
        self._kb_cache = None
        return True

    # ------------------------------------------------------------------ #
    # Queries                                                            #
    # ------------------------------------------------------------------ #

    def all_plugins(self) -> list[LoadedPlugin]:
        """Return all loaded plugins (enabled and disabled), sorted by name."""
        return [self._plugins[name] for name in sorted(self._plugins)]

    def enabled_plugins(self) -> list[AnalyzerPlugin]:
        """Return enabled plugin instances, sorted by name."""
        return [lp.plugin for name, lp in sorted(self._plugins.items()) if lp.enabled]

    def get(self, name: str) -> AnalyzerPlugin | None:
        """Return a plugin by name regardless of enabled state."""
        loaded = self._plugins.get(name)
        return loaded.plugin if loaded else None

    def is_enabled(self, name: str) -> bool:
        """Return True if the named plugin is loaded and enabled."""
        loaded = self._plugins.get(name)
        return bool(loaded and loaded.enabled)

    def failures(self) -> list[PluginFailure]:
        """Return the list of plugins that failed to load or were incompatible."""
        return list(self._failures)

    def plugin_for(
        self,
        content: str,
        *,
        technology: Technology | None = None,
        source_kind: SourceKind | None = None,
        filename: str | None = None,
    ) -> AnalyzerPlugin | None:
        """Return the first enabled plugin that supports the given input."""
        for plugin in self.enabled_plugins():
            if plugin.supports(
                content, technology=technology, source_kind=source_kind, filename=filename
            ):
                return plugin
        return None

    def plugin_for_technology(self, technology: Technology) -> AnalyzerPlugin | None:
        """Return the enabled plugin that owns ``technology``, if any."""
        for plugin in self.enabled_plugins():
            if technology in plugin.metadata().supported_technologies:
                return plugin
        return None

    def aggregate_signatures(self) -> list[Signature]:
        """Collect signatures from every enabled plugin."""
        signatures: list[Signature] = []
        seen: set[str] = set()
        for plugin in self.enabled_plugins():
            for sig in plugin.signatures():
                if sig.id not in seen:
                    seen.add(sig.id)
                    signatures.append(sig)
        return signatures

    def aggregate_knowledge_base(self) -> KnowledgeBase:
        """Return a cached knowledge base spanning all enabled plugins."""
        if self._kb_cache is None:
            self._kb_cache = KnowledgeBase(self.aggregate_signatures())
        return self._kb_cache

    def doctor(self) -> dict[str, object]:
        """Return a health report: counts, incompatibilities and load failures."""
        return {
            "core_version": self.core_version,
            "loaded": len(self._plugins),
            "enabled": sum(1 for lp in self._plugins.values() if lp.enabled),
            "signatures": len(self.aggregate_signatures()),
            "failures": [
                {"name": f.name, "source": f.source, "reason": f.reason} for f in self._failures
            ],
        }
