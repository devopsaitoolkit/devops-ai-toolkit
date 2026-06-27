"""Tests for the :class:`PluginManager` discovery, lifecycle and aggregation."""

from __future__ import annotations

from devops_ai_toolkit.models.enums import Technology
from devops_ai_toolkit.models.knowledge import MatchSpec, Signature
from devops_ai_toolkit.plugins.knowledge_backed import KnowledgeBackedPlugin
from devops_ai_toolkit.plugins.manager import PluginManager
from devops_ai_toolkit.plugins.metadata import PluginMetadata


def _make_plugin(
    name: str,
    *,
    technology: Technology = Technology.UNKNOWN,
    minimum_core_version: str = "0.1.0",
    sig_id: str = "custom.error",
) -> KnowledgeBackedPlugin:
    meta = PluginMetadata(
        name=name,
        minimum_core_version=minimum_core_version,
        supported_technologies=[technology],
    )
    signatures = [
        Signature(
            id=sig_id,
            technology=technology,
            title="Custom error",
            summary="A hand-made signature.",
            match=MatchSpec(any_of=["zzz-custom-marker"], weight=0.5),
        )
    ]
    return KnowledgeBackedPlugin(meta, signatures)


def test_create_default_loads_many_builtins_with_no_failures() -> None:
    manager = PluginManager.create_default()
    loaded = manager.all_plugins()
    assert len(loaded) >= 20
    assert manager.failures() == []
    for lp in loaded:
        assert lp.source == "builtin"
        assert lp.enabled is True


def test_aggregate_signatures_match_full_knowledge_base() -> None:
    from devops_ai_toolkit.knowledge.loader import load_default_knowledge_base

    manager = PluginManager.create_default()
    sigs = manager.aggregate_signatures()
    full = load_default_knowledge_base().signatures
    assert len(sigs) == len(full)
    # No duplicate ids in the aggregate knowledge base.
    ids = [s.id for s in manager.aggregate_knowledge_base().signatures]
    assert len(ids) == len(set(ids))


def test_enable_disable_toggles_state_and_aggregation() -> None:
    manager = PluginManager.create_default()
    before_enabled = len(manager.enabled_plugins())
    before_sigs = len(manager.aggregate_signatures())

    docker = manager.get("docker")
    assert docker is not None
    docker_sig_count = len(docker.signatures())
    assert docker_sig_count > 0

    assert manager.is_enabled("docker") is True
    assert manager.disable("docker") is True
    assert manager.is_enabled("docker") is False
    assert len(manager.enabled_plugins()) == before_enabled - 1
    assert len(manager.aggregate_signatures()) == before_sigs - docker_sig_count

    assert manager.enable("docker") is True
    assert manager.is_enabled("docker") is True
    assert len(manager.enabled_plugins()) == before_enabled
    assert len(manager.aggregate_signatures()) == before_sigs


def test_enable_disable_unknown_returns_false() -> None:
    manager = PluginManager.create_default()
    assert manager.disable("does-not-exist") is False
    assert manager.enable("does-not-exist") is False


def test_disabling_removes_technology_routing() -> None:
    manager = PluginManager.create_default()
    assert manager.plugin_for_technology(Technology.DOCKER) is not None
    manager.disable("docker")
    assert manager.plugin_for_technology(Technology.DOCKER) is None
    manager.enable("docker")
    assert manager.plugin_for_technology(Technology.DOCKER) is not None


def test_register_duplicate_name_records_failure() -> None:
    manager = PluginManager.create_default()
    before = len(manager.all_plugins())
    # Re-register the docker name from a manual source: should be ignored.
    dup = _make_plugin("docker", technology=Technology.DOCKER, sig_id="dup.docker")
    manager.register(dup)
    assert len(manager.all_plugins()) == before
    failures = manager.failures()
    assert any(f.name == "docker" and "duplicate" in f.reason for f in failures)


def test_incompatible_plugin_recorded_and_not_loaded() -> None:
    manager = PluginManager()  # empty manager
    incompatible = _make_plugin("future-plugin", minimum_core_version="99.0.0", sig_id="future.err")
    manager.register(incompatible)
    assert manager.get("future-plugin") is None
    failures = manager.failures()
    assert any(
        f.name == "future-plugin" and "requires core >= 99.0.0" in f.reason for f in failures
    )


def test_register_compatible_custom_plugin_loads() -> None:
    manager = PluginManager()
    plugin = _make_plugin("my-custom", technology=Technology.REDIS, sig_id="my.custom")
    manager.register(plugin, source="manual")
    assert manager.get("my-custom") is plugin
    assert manager.is_enabled("my-custom") is True
    assert manager.all_plugins()[0].source == "manual"


def test_doctor_returns_expected_keys() -> None:
    manager = PluginManager.create_default()
    report = manager.doctor()
    assert set(report.keys()) == {
        "core_version",
        "loaded",
        "enabled",
        "signatures",
        "failures",
    }
    assert report["loaded"] >= 20
    assert report["enabled"] == report["loaded"]
    assert isinstance(report["failures"], list)
    assert report["signatures"] == len(manager.aggregate_signatures())
