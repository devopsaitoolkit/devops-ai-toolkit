"""Built-in terraform analyzer plugin."""

from __future__ import annotations

from ...models.enums import Technology
from ...validators.terraform import validate_terraform
from ..metadata import PluginMetadata
from ._common import build

PLUGIN = build(
    PluginMetadata(
        name="terraform",
        version="0.1.0",
        description="Terraform state, provider, and configuration errors.",
        author="DevOps AI Toolkit",
        homepage="https://devopsaitoolkit.com",
        repository="https://github.com/devopsaitoolkit/devops-ai-toolkit",
        documentation="https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md",
        license="MIT",
        minimum_core_version="0.1.0",
        builtin=True,
        tags=["terraform", "iac", "hcl"],
        supported_platforms=["linux", "macos", "windows"],
        supported_technologies=[Technology.TERRAFORM],
        supported_file_types=[".tf", ".txt", ".log"],
        supported_commands=["terraform plan", "terraform validate", "terraform show"],
    ),
    validator=validate_terraform,
)
