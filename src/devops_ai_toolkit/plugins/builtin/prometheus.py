"""Built-in prometheus analyzer plugin."""

from __future__ import annotations

from ...models.enums import Technology
from ...validators.yaml_validator import validate_yaml
from ..metadata import PluginMetadata
from ._common import build

PLUGIN = build(
    PluginMetadata(
        name="prometheus",
        version="0.1.0",
        description="Prometheus scrape, PromQL, TSDB, and alerting errors.",
        author="DevOps AI Toolkit",
        homepage="https://devopsaitoolkit.com",
        repository="https://github.com/devopsaitoolkit/devops-ai-toolkit",
        documentation="https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md",
        license="MIT",
        minimum_core_version="0.1.0",
        builtin=True,
        tags=["prometheus", "monitoring", "observability"],
        supported_platforms=["linux", "macos", "windows"],
        supported_technologies=[Technology.PROMETHEUS],
        supported_file_types=[".yml", ".yaml", ".log"],
        supported_commands=["promtool check config", "promtool check rules"],
    ),
    validator=validate_yaml,
)
