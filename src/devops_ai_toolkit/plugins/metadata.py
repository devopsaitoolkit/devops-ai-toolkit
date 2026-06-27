"""Plugin metadata — the marketplace and enterprise descriptor for a plugin.

Every plugin declares one :class:`PluginMetadata`. The fields are a superset of
what a future plugin marketplace and enterprise registry need (authorship,
licensing, compatibility, signing), so plugins are publishable without any
later schema change.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .._version import __version__
from ..models.enums import Technology


def _parse_version(value: str) -> tuple[int, ...]:
    """Parse a dotted version into a comparable integer tuple (best effort)."""
    parts: list[int] = []
    for chunk in value.split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) or (0,)


class PluginMetadata(BaseModel):
    """Self-describing metadata for an analyzer plugin.

    The marketplace block (name/version/author/homepage/description/license/
    minimum_core_version/tags/supported_platforms/documentation/repository) is
    exactly what an online registry would index. The capability block tells the
    plugin manager which inputs a plugin can handle. The enterprise block
    (``signed``/``checksum``) supports private, signed distribution.
    """

    # --- marketplace ---
    name: str = Field(description="Unique plugin name, e.g. 'docker'.")
    version: str = Field(default="0.1.0")
    description: str = ""
    author: str = ""
    homepage: str = ""
    repository: str = ""
    documentation: str = ""
    license: str = "MIT"
    minimum_core_version: str = Field(
        default="0.1.0",
        description="Lowest devops-ai-toolkit core version this plugin supports.",
    )
    tags: list[str] = Field(default_factory=list)
    supported_platforms: list[str] = Field(default_factory=lambda: ["linux", "macos", "windows"])

    # --- capabilities ---
    supported_technologies: list[Technology] = Field(default_factory=list)
    supported_file_types: list[str] = Field(
        default_factory=list, description="File extensions, e.g. ['.log', '.yaml']."
    )
    supported_commands: list[str] = Field(
        default_factory=list, description="CLI commands whose output this plugin understands."
    )

    # --- enterprise / supply chain ---
    builtin: bool = Field(default=False, description="True for plugins shipped with the core.")
    signed: bool = Field(
        default=False, description="True when the plugin ships a verified checksum."
    )
    checksum: str | None = Field(default=None, description="Optional sha256 of the plugin payload.")

    def is_compatible(self, core_version: str = __version__) -> bool:
        """Return True if ``core_version`` satisfies ``minimum_core_version``."""
        return _parse_version(core_version) >= _parse_version(self.minimum_core_version)
