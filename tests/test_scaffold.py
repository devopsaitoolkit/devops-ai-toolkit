"""Tests for the plugin scaffolder (``devops-ai create-plugin``)."""

from __future__ import annotations

from pathlib import Path

from devops_ai_toolkit.cli.scaffold import _normalise, create_plugin


def test_name_normalisation() -> None:
    dist, package = _normalise("My Cool Plugin")
    assert dist == "my-cool-plugin"
    assert package == "my_cool_plugin"


def test_create_plugin_creates_expected_files(tmp_path: Path) -> None:
    root = create_plugin("My Cool Plugin", tmp_path)
    assert root == tmp_path / "my-cool-plugin"
    assert root.is_dir()

    pyproject = root / "pyproject.toml"
    plugin_py = root / "my_cool_plugin" / "plugin.py"
    init_py = root / "my_cool_plugin" / "__init__.py"
    test_py = root / "tests" / "test_plugin.py"

    for path in (pyproject, plugin_py, init_py, test_py):
        assert path.is_file(), f"missing {path}"

    py_text = pyproject.read_text(encoding="utf-8")
    assert '[project.entry-points."devops_ai_toolkit.plugins"]' in py_text
    assert 'my-cool-plugin = "my_cool_plugin.plugin:PLUGIN"' in py_text
    assert 'name = "my-cool-plugin"' in py_text

    plugin_text = plugin_py.read_text(encoding="utf-8")
    assert "PLUGIN =" in plugin_text
    assert "KnowledgeBackedPlugin" in plugin_text


def test_generated_plugin_py_is_importable(tmp_path: Path) -> None:
    root = create_plugin("Another Plugin", tmp_path)
    plugin_py = root / "another_plugin" / "plugin.py"
    namespace: dict[str, object] = {}
    code = compile(plugin_py.read_text(encoding="utf-8"), str(plugin_py), "exec")
    exec(code, namespace)
    from devops_ai_toolkit.plugins.base import AnalyzerPlugin

    plugin = namespace["PLUGIN"]
    assert isinstance(plugin, AnalyzerPlugin)
    assert plugin.metadata().name == "another-plugin"


def test_create_plugin_blank_name_defaults(tmp_path: Path) -> None:
    dist, package = _normalise("   ")
    assert dist == "my-plugin"
    assert package == "my_plugin"
