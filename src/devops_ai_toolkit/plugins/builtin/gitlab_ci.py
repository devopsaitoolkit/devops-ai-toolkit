"""Built-in gitlab-ci analyzer plugin."""

from __future__ import annotations

from ...models.enums import Technology
from ...validators.yaml_validator import validate_yaml
from ..metadata import PluginMetadata
from ._common import build

PLUGIN = build(
    PluginMetadata(
        name="gitlab-ci",
        version="0.1.0",
        description="GitLab CI/CD pipeline, runner, and registry errors.",
        author="DevOps AI Toolkit",
        homepage="https://devopsaitoolkit.com",
        repository="https://github.com/devopsaitoolkit/devops-ai-toolkit",
        documentation="https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md",
        license="MIT",
        minimum_core_version="0.1.0",
        builtin=True,
        tags=["gitlab", "ci-cd", "pipelines"],
        supported_platforms=["linux", "macos", "windows"],
        supported_technologies=[Technology.GITLAB_CI],
        supported_file_types=[".yml", ".yaml", ".log"],
        supported_commands=["gitlab-runner verify"],
    ),
    validator=validate_yaml,
)
