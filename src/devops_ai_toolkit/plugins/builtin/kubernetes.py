"""Built-in kubernetes analyzer plugin."""

from __future__ import annotations

from ...models.enums import Technology
from ...validators.kubernetes import validate_kubernetes
from ..metadata import PluginMetadata
from ._common import build

PLUGIN = build(
    PluginMetadata(
        name="kubernetes",
        version="0.1.0",
        description="Kubernetes & OpenShift pod, scheduling, and manifest errors.",
        author="DevOps AI Toolkit",
        homepage="https://devopsaitoolkit.com",
        repository="https://github.com/devopsaitoolkit/devops-ai-toolkit",
        documentation="https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md",
        license="MIT",
        minimum_core_version="0.1.0",
        builtin=True,
        tags=["kubernetes", "k8s", "openshift", "containers"],
        supported_platforms=["linux", "macos", "windows"],
        supported_technologies=[Technology.KUBERNETES, Technology.OPENSHIFT],
        supported_file_types=[".yaml", ".yml", ".log"],
        supported_commands=["kubectl describe", "kubectl logs", "kubectl get events"],
    ),
    validator=validate_kubernetes,
)
