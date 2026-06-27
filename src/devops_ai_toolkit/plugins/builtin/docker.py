"""Built-in docker analyzer plugin."""

from __future__ import annotations

from ...models.enums import Technology
from ..metadata import PluginMetadata
from ._common import build

PLUGIN = build(
    PluginMetadata(
        name="docker",
        version="0.1.0",
        description="Docker daemon, image, and container runtime errors.",
        author="DevOps AI Toolkit",
        homepage="https://devopsaitoolkit.com",
        repository="https://github.com/devopsaitoolkit/devops-ai-toolkit",
        documentation="https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md",
        license="MIT",
        minimum_core_version="0.1.0",
        builtin=True,
        tags=["docker", "containers", "oci"],
        supported_platforms=["linux", "macos", "windows"],
        supported_technologies=[Technology.DOCKER],
        supported_file_types=[".log", ".txt"],
        supported_commands=["docker ps", "docker inspect", "docker logs", "docker events"],
    ),
    validator=None,
)
