"""Tests for the ``devops-ai plugins`` CLI command group and create-plugin."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from devops_ai_toolkit.cli.app import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def isolated_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the plugin enable/disable state file at a throwaway path."""
    state = tmp_path / "plugins-state.json"
    monkeypatch.setenv("DEVOPS_AI_STATE", str(state))
    return state


def test_plugins_list() -> None:
    result = runner.invoke(app, ["plugins", "list"])
    assert result.exit_code == 0
    assert "docker" in result.stdout
    assert "kubernetes" in result.stdout
    assert "Plugins" in result.stdout


def test_plugins_info_docker() -> None:
    result = runner.invoke(app, ["plugins", "info", "docker"])
    assert result.exit_code == 0
    assert "docker" in result.stdout


def test_plugins_info_unknown() -> None:
    result = runner.invoke(app, ["plugins", "info", "no-such-plugin"])
    assert result.exit_code == 1
    assert "Unknown plugin" in result.stdout


def test_plugins_doctor() -> None:
    result = runner.invoke(app, ["plugins", "doctor"])
    assert result.exit_code == 0
    assert "core_version" in result.stdout
    assert "loaded" in result.stdout


def test_disable_then_list_then_enable() -> None:
    disabled = runner.invoke(app, ["plugins", "disable", "docker"])
    assert disabled.exit_code == 0
    assert "Disabled" in disabled.stdout

    listed = runner.invoke(app, ["plugins", "list"])
    assert listed.exit_code == 0
    assert "disabled" in listed.stdout

    enabled = runner.invoke(app, ["plugins", "enable", "docker"])
    assert enabled.exit_code == 0
    assert "Enabled" in enabled.stdout


def test_create_plugin_command(tmp_path: Path) -> None:
    result = runner.invoke(app, ["create-plugin", "tmpname", "--dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "Created plugin project" in result.stdout
    assert (tmp_path / "tmpname" / "pyproject.toml").is_file()
    assert (tmp_path / "tmpname" / "tmpname" / "plugin.py").is_file()
