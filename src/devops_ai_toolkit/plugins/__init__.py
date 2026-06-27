"""The plugin system: interface, metadata, base implementations and manager.

Every supported technology is an independent :class:`AnalyzerPlugin`. The
:class:`PluginManager` discovers them (built-in modules + third-party entry
points) so the core engine contains no technology-specific logic and needs no
changes when new plugins are installed.
"""

from __future__ import annotations

from .base import AnalyzerPlugin
from .knowledge_backed import KnowledgeBackedPlugin
from .manager import ENTRY_POINT_GROUP, LoadedPlugin, PluginFailure, PluginManager
from .metadata import PluginMetadata

__all__ = [
    "ENTRY_POINT_GROUP",
    "AnalyzerPlugin",
    "KnowledgeBackedPlugin",
    "LoadedPlugin",
    "PluginFailure",
    "PluginManager",
    "PluginMetadata",
]
