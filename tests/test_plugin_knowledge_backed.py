"""Tests for :class:`KnowledgeBackedPlugin` built from hand-made signatures."""

from __future__ import annotations

import pytest

from devops_ai_toolkit.models.enums import Technology
from devops_ai_toolkit.models.knowledge import CauseTemplate, MatchSpec, Signature
from devops_ai_toolkit.plugins.knowledge_backed import KnowledgeBackedPlugin
from devops_ai_toolkit.plugins.metadata import PluginMetadata


@pytest.fixture
def plugin() -> KnowledgeBackedPlugin:
    meta = PluginMetadata(
        name="widget",
        supported_technologies=[Technology.REDIS],
        supported_file_types=[".widget"],
    )
    signatures = [
        Signature(
            id="widget.overheat",
            technology=Technology.REDIS,
            title="Widget overheated",
            summary="The widget exceeded its safe temperature.",
            match=MatchSpec(any_of=[r"widget overheated"], weight=0.8),
            root_causes=[
                CauseTemplate(
                    title="Fan failure",
                    description="The cooling fan stopped.",
                    confidence=0.7,
                    category="hardware",
                )
            ],
            best_practices=["Check the fan monthly."],
            prevention=["Install a temperature alarm."],
        ),
        Signature(
            id="widget.jammed",
            technology=Technology.REDIS,
            title="Widget jammed",
            summary="The widget mechanism jammed.",
            match=MatchSpec(any_of=[r"widget jammed"], weight=0.6),
        ),
    ]
    return KnowledgeBackedPlugin(meta, signatures)


def test_supports_matching_technology(plugin: KnowledgeBackedPlugin) -> None:
    assert plugin.supports("anything", technology=Technology.REDIS) is True


def test_supports_matching_file_type(plugin: KnowledgeBackedPlugin) -> None:
    assert plugin.supports("anything", filename="gadget.widget") is True


def test_supports_matching_content(plugin: KnowledgeBackedPlugin) -> None:
    assert plugin.supports("the widget overheated badly") is True


def test_supports_false_for_benign_text(plugin: KnowledgeBackedPlugin) -> None:
    assert plugin.supports("everything is fine here") is False


def test_analyze_returns_matched_result(plugin: KnowledgeBackedPlugin) -> None:
    result = plugin.analyze("log line: widget overheated at 12:00")
    assert result.matched is True
    assert "widget.overheat" in result.signatures_matched
    assert result.technology is Technology.REDIS
    assert result.metadata  # engine label populated


def test_analyze_benign_text_no_match(plugin: KnowledgeBackedPlugin) -> None:
    result = plugin.analyze("everything is fine")
    assert result.matched is False
    assert result.signatures_matched == []


def test_validate_falls_back_to_yaml(plugin: KnowledgeBackedPlugin) -> None:
    # No validator supplied -> generic YAML validation.
    valid = plugin.validate("key: value\nother: 1\n")
    assert valid.valid is True
    invalid = plugin.validate("key: : : bad\n\t- tab\n")
    assert invalid.valid is False


def test_explain_known_id(plugin: KnowledgeBackedPlugin) -> None:
    explained = plugin.explain("widget.overheat")
    assert explained is not None
    assert explained.title == "Widget overheated"
    assert explained.technology is Technology.REDIS
    assert explained.root_causes
    assert explained.root_causes[0].title == "Fan failure"


def test_explain_unknown_returns_none(plugin: KnowledgeBackedPlugin) -> None:
    assert plugin.explain("no-such-signature-xyz") is None


def test_extract_errors(plugin: KnowledgeBackedPlugin) -> None:
    errors = plugin.extract_errors("first line\nwidget overheated now\nlast line")
    assert any("widget overheated" in e for e in errors)


def test_extract_warnings(plugin: KnowledgeBackedPlugin) -> None:
    warnings = plugin.extract_warnings(
        "all good\nWARNING: disk almost full\nthis API is deprecated soon\n"
    )
    assert len(warnings) >= 2
    assert any("WARNING" in w for w in warnings)


def test_extract_resources(plugin: KnowledgeBackedPlugin) -> None:
    resources = plugin.extract_resources("pod default/web-123 crashed; container app restarted")
    assert resources  # at least one resource id extracted
    assert isinstance(resources, list)


def test_extract_recommendations(plugin: KnowledgeBackedPlugin) -> None:
    result = plugin.analyze("widget overheated")
    recs = plugin.extract_recommendations(result)
    assert "Check the fan monthly." in recs
    assert "Install a temperature alarm." in recs
    # No duplicates.
    assert len(recs) == len(set(recs))
