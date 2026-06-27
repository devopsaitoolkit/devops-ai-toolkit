"""Built-in gcp analyzer plugin."""

from __future__ import annotations

from ...models.enums import Technology
from ..metadata import PluginMetadata
from ._common import build

PLUGIN = build(
    PluginMetadata(
        name="gcp",
        version="0.1.0",
        description="Google Cloud IAM, quota, and resource errors.",
        author="DevOps AI Toolkit",
        homepage="https://devopsaitoolkit.com",
        repository="https://github.com/devopsaitoolkit/devops-ai-toolkit",
        documentation="https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md",
        license="MIT",
        minimum_core_version="0.1.0",
        builtin=True,
        tags=["gcp", "google-cloud", "gke", "cloud"],
        supported_platforms=["linux", "macos", "windows"],
        supported_technologies=[Technology.GCP],
        supported_file_types=[".log"],
        supported_commands=["gcloud auth list"],
    ),
    validator=None,
)
