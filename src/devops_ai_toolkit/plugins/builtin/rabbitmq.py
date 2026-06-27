"""Built-in rabbitmq analyzer plugin."""

from __future__ import annotations

from ...models.enums import Technology
from ..metadata import PluginMetadata
from ._common import build

PLUGIN = build(
    PluginMetadata(
        name="rabbitmq",
        version="0.1.0",
        description="RabbitMQ connectivity, memory alarm, and partition errors.",
        author="DevOps AI Toolkit",
        homepage="https://devopsaitoolkit.com",
        repository="https://github.com/devopsaitoolkit/devops-ai-toolkit",
        documentation="https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md",
        license="MIT",
        minimum_core_version="0.1.0",
        builtin=True,
        tags=["rabbitmq", "messaging", "amqp"],
        supported_platforms=["linux", "macos", "windows"],
        supported_technologies=[Technology.RABBITMQ],
        supported_file_types=[".log"],
        supported_commands=["rabbitmqctl status", "rabbitmqctl list_queues"],
    ),
    validator=None,
)
