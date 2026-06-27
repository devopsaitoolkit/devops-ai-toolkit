"""Built-in postgresql analyzer plugin."""

from __future__ import annotations

from ...models.enums import Technology
from ..metadata import PluginMetadata
from ._common import build

PLUGIN = build(
    PluginMetadata(
        name="postgresql",
        version="0.1.0",
        description="PostgreSQL connection, role, disk, and lock errors.",
        author="DevOps AI Toolkit",
        homepage="https://devopsaitoolkit.com",
        repository="https://github.com/devopsaitoolkit/devops-ai-toolkit",
        documentation="https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md",
        license="MIT",
        minimum_core_version="0.1.0",
        builtin=True,
        tags=["postgresql", "postgres", "database"],
        supported_platforms=["linux", "macos", "windows"],
        supported_technologies=[Technology.POSTGRESQL],
        supported_file_types=[".log"],
        supported_commands=["psql -c 'SELECT 1'", "pg_isready"],
    ),
    validator=None,
)
