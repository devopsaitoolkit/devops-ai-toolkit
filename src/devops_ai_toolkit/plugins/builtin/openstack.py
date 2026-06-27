"""Built-in openstack analyzer plugin."""

from __future__ import annotations

from ...models.enums import Technology
from ..metadata import PluginMetadata
from ._common import build

PLUGIN = build(
    PluginMetadata(
        name="openstack",
        version="0.1.0",
        description="OpenStack Nova, Cinder, Neutron, and Keystone errors.",
        author="DevOps AI Toolkit",
        homepage="https://devopsaitoolkit.com",
        repository="https://github.com/devopsaitoolkit/devops-ai-toolkit",
        documentation="https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md",
        license="MIT",
        minimum_core_version="0.1.0",
        builtin=True,
        tags=["openstack", "nova", "cinder", "neutron", "cloud"],
        supported_platforms=["linux", "macos", "windows"],
        supported_technologies=[Technology.OPENSTACK],
        supported_file_types=[".log", ".txt"],
        supported_commands=["openstack server show", "openstack hypervisor list"],
    ),
    validator=None,
)
