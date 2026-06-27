"""Tests for :class:`PluginMetadata` and version compatibility."""

from __future__ import annotations

from devops_ai_toolkit._version import __version__
from devops_ai_toolkit.models.enums import Technology
from devops_ai_toolkit.plugins.metadata import PluginMetadata


def test_metadata_defaults() -> None:
    meta = PluginMetadata(name="example")
    assert meta.name == "example"
    assert meta.version == "0.1.0"
    assert meta.description == ""
    assert meta.author == ""
    assert meta.license == "MIT"
    assert meta.minimum_core_version == "0.1.0"
    assert meta.tags == []
    assert meta.supported_platforms == ["linux", "macos", "windows"]
    assert meta.supported_technologies == []
    assert meta.supported_file_types == []
    assert meta.supported_commands == []
    assert meta.builtin is False
    assert meta.signed is False
    assert meta.checksum is None


def test_is_compatible_true_when_core_meets_minimum() -> None:
    meta = PluginMetadata(name="example", minimum_core_version="0.1.0")
    assert meta.is_compatible(__version__) is True
    # Explicit higher core version also satisfies a low minimum.
    assert meta.is_compatible("1.0.0") is True
    # Default argument uses the running core version.
    assert meta.is_compatible() is True


def test_is_compatible_false_when_core_below_minimum() -> None:
    meta = PluginMetadata(name="example", minimum_core_version="99.0.0")
    assert meta.is_compatible(__version__) is False
    assert meta.is_compatible("0.0.1") is False


def test_model_dump_round_trip() -> None:
    meta = PluginMetadata(
        name="roundtrip",
        version="1.2.3",
        description="A plugin",
        author="Tester",
        tags=["a", "b"],
        supported_technologies=[Technology.DOCKER, Technology.KUBERNETES],
        supported_file_types=[".log", ".yaml"],
        supported_commands=["docker ps"],
        builtin=True,
        minimum_core_version="0.1.0",
    )
    dumped = meta.model_dump()
    restored = PluginMetadata(**dumped)
    assert restored == meta
    assert restored.model_dump() == dumped
    # JSON round-trip as well.
    restored_json = PluginMetadata.model_validate_json(meta.model_dump_json())
    assert restored_json == meta
