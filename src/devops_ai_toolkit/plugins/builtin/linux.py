"""Built-in linux analyzer plugin."""

from __future__ import annotations

from ...models.enums import Technology
from ..metadata import PluginMetadata
from ._common import build

PLUGIN = build(
    PluginMetadata(
        name="linux",
        version="0.1.0",
        description="Linux kernel, memory, disk, and filesystem errors.",
        author="DevOps AI Toolkit",
        homepage="https://devopsaitoolkit.com",
        repository="https://github.com/devopsaitoolkit/devops-ai-toolkit",
        documentation="https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md",
        license="MIT",
        minimum_core_version="0.1.0",
        builtin=True,
        tags=["linux", "kernel", "sysadmin"],
        supported_platforms=["linux", "macos", "windows"],
        supported_technologies=[Technology.LINUX],
        supported_file_types=[".log"],
        supported_commands=["dmesg", "journalctl", "df", "free"],
    ),
    validator=None,
)
