"""Built-in linstor analyzer plugin."""

from __future__ import annotations

from ...models.enums import Technology
from ..metadata import PluginMetadata
from ._common import build

PLUGIN = build(
    PluginMetadata(
        name="linstor",
        version="0.1.0",
        description="LINSTOR satellite and resource-placement errors.",
        author="DevOps AI Toolkit",
        homepage="https://devopsaitoolkit.com",
        repository="https://github.com/devopsaitoolkit/devops-ai-toolkit",
        documentation="https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md",
        license="MIT",
        minimum_core_version="0.1.0",
        builtin=True,
        tags=["linstor", "drbd", "storage"],
        supported_platforms=["linux", "macos", "windows"],
        supported_technologies=[Technology.LINSTOR],
        supported_file_types=[".log"],
        supported_commands=["linstor node list", "linstor storage-pool list"],
    ),
    validator=None,
)
