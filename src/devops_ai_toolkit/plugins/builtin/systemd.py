"""Built-in systemd analyzer plugin."""

from __future__ import annotations

from ...models.enums import Technology
from ..metadata import PluginMetadata
from ._common import build

PLUGIN = build(
    PluginMetadata(
        name="systemd",
        version="0.1.0",
        description="systemd unit start, dependency, and exit-code failures.",
        author="DevOps AI Toolkit",
        homepage="https://devopsaitoolkit.com",
        repository="https://github.com/devopsaitoolkit/devops-ai-toolkit",
        documentation="https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md",
        license="MIT",
        minimum_core_version="0.1.0",
        builtin=True,
        tags=["systemd", "services", "init"],
        supported_platforms=["linux", "macos", "windows"],
        supported_technologies=[Technology.SYSTEMD],
        supported_file_types=[".log"],
        supported_commands=["systemctl status", "journalctl -u"],
    ),
    validator=None,
)
