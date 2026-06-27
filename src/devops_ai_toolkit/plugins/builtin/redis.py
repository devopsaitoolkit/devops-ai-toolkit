"""Built-in redis analyzer plugin."""

from __future__ import annotations

from ...models.enums import Technology
from ..metadata import PluginMetadata
from ._common import build

PLUGIN = build(
    PluginMetadata(
        name="redis",
        version="0.1.0",
        description="Redis persistence, memory, and authentication errors.",
        author="DevOps AI Toolkit",
        homepage="https://devopsaitoolkit.com",
        repository="https://github.com/devopsaitoolkit/devops-ai-toolkit",
        documentation="https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md",
        license="MIT",
        minimum_core_version="0.1.0",
        builtin=True,
        tags=["redis", "cache", "kv"],
        supported_platforms=["linux", "macos", "windows"],
        supported_technologies=[Technology.REDIS],
        supported_file_types=[".log", ".conf"],
        supported_commands=["redis-cli INFO", "redis-cli PING"],
    ),
    validator=None,
)
