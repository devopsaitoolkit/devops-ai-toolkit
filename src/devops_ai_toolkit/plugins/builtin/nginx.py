"""Built-in nginx analyzer plugin."""

from __future__ import annotations

from ...models.enums import Technology
from ..metadata import PluginMetadata
from ._common import build

PLUGIN = build(
    PluginMetadata(
        name="nginx",
        version="0.1.0",
        description="NGINX upstream, permission, binding, and timeout errors.",
        author="DevOps AI Toolkit",
        homepage="https://devopsaitoolkit.com",
        repository="https://github.com/devopsaitoolkit/devops-ai-toolkit",
        documentation="https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md",
        license="MIT",
        minimum_core_version="0.1.0",
        builtin=True,
        tags=["nginx", "proxy", "web", "reverse-proxy"],
        supported_platforms=["linux", "macos", "windows"],
        supported_technologies=[Technology.NGINX],
        supported_file_types=[".log", ".conf"],
        supported_commands=["nginx -t", "nginx -T"],
    ),
    validator=None,
)
