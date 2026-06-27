"""Built-in vmware analyzer plugin."""

from __future__ import annotations

from ...models.enums import Technology
from ..metadata import PluginMetadata
from ._common import build

PLUGIN = build(
    PluginMetadata(
        name="vmware",
        version="0.1.0",
        description="VMware vSphere HA capacity and ESXi connectivity errors.",
        author="DevOps AI Toolkit",
        homepage="https://devopsaitoolkit.com",
        repository="https://github.com/devopsaitoolkit/devops-ai-toolkit",
        documentation="https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md",
        license="MIT",
        minimum_core_version="0.1.0",
        builtin=True,
        tags=["vmware", "vsphere", "esxi", "virtualization"],
        supported_platforms=["linux", "macos", "windows"],
        supported_technologies=[Technology.VMWARE],
        supported_file_types=[".log"],
        supported_commands=["esxcli system maintenanceMode get"],
    ),
    validator=None,
)
