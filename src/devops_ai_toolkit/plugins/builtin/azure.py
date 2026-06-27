"""Built-in azure analyzer plugin."""

from __future__ import annotations

from ...models.enums import Technology
from ..metadata import PluginMetadata
from ._common import build

PLUGIN = build(
    PluginMetadata(
        name="azure",
        version="0.1.0",
        description="Azure authentication, quota, and resource errors.",
        author="DevOps AI Toolkit",
        homepage="https://devopsaitoolkit.com",
        repository="https://github.com/devopsaitoolkit/devops-ai-toolkit",
        documentation="https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md",
        license="MIT",
        minimum_core_version="0.1.0",
        builtin=True,
        tags=["azure", "cloud"],
        supported_platforms=["linux", "macos", "windows"],
        supported_technologies=[Technology.AZURE],
        supported_file_types=[".log", ".json"],
        supported_commands=["az account show"],
    ),
    validator=None,
)
