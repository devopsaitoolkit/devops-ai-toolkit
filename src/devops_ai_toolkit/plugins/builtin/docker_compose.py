"""Built-in docker-compose analyzer plugin."""

from __future__ import annotations

from ...models.enums import Technology
from ...validators.yaml_validator import validate_yaml
from ..metadata import PluginMetadata
from ._common import build

PLUGIN = build(
    PluginMetadata(
        name="docker-compose",
        version="0.1.0",
        description="Docker Compose file validation and multi-container errors.",
        author="DevOps AI Toolkit",
        homepage="https://devopsaitoolkit.com",
        repository="https://github.com/devopsaitoolkit/devops-ai-toolkit",
        documentation="https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md",
        license="MIT",
        minimum_core_version="0.1.0",
        builtin=True,
        tags=["docker-compose", "compose", "containers"],
        supported_platforms=["linux", "macos", "windows"],
        supported_technologies=[Technology.DOCKER_COMPOSE],
        supported_file_types=[".yml", ".yaml"],
        supported_commands=["docker compose up", "docker compose config"],
    ),
    validator=validate_yaml,
)
