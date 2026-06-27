"""Built-in mysql analyzer plugin."""

from __future__ import annotations

from ...models.enums import Technology
from ..metadata import PluginMetadata
from ._common import build

PLUGIN = build(
    PluginMetadata(
        name="mysql",
        version="0.1.0",
        description="MySQL/MariaDB access, connection, and disk errors.",
        author="DevOps AI Toolkit",
        homepage="https://devopsaitoolkit.com",
        repository="https://github.com/devopsaitoolkit/devops-ai-toolkit",
        documentation="https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md",
        license="MIT",
        minimum_core_version="0.1.0",
        builtin=True,
        tags=["mysql", "mariadb", "database"],
        supported_platforms=["linux", "macos", "windows"],
        supported_technologies=[Technology.MYSQL],
        supported_file_types=[".log"],
        supported_commands=["mysqladmin status"],
    ),
    validator=None,
)
