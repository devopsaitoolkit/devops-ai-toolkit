"""Built-in ceph analyzer plugin."""

from __future__ import annotations

from ...models.enums import Technology
from ..metadata import PluginMetadata
from ._common import build

PLUGIN = build(
    PluginMetadata(
        name="ceph",
        version="0.1.0",
        description="Ceph cluster health, OSD, and placement-group errors.",
        author="DevOps AI Toolkit",
        homepage="https://devopsaitoolkit.com",
        repository="https://github.com/devopsaitoolkit/devops-ai-toolkit",
        documentation="https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md",
        license="MIT",
        minimum_core_version="0.1.0",
        builtin=True,
        tags=["ceph", "storage", "distributed"],
        supported_platforms=["linux", "macos", "windows"],
        supported_technologies=[Technology.CEPH],
        supported_file_types=[".log"],
        supported_commands=["ceph status", "ceph health detail"],
    ),
    validator=None,
)
