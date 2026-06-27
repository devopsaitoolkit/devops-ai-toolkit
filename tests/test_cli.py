"""Tests for the Typer CLI app via CliRunner."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from devops_ai_toolkit.cli.app import app

runner = CliRunner()


@pytest.fixture
def log_file(tmp_path, crashloop_log):
    p = tmp_path / "crash.log"
    p.write_text(crashloop_log, encoding="utf-8")
    return p


class TestAnalyze:
    def test_analyze_file_match(self, log_file):
        result = runner.invoke(app, ["analyze", str(log_file)])
        assert result.exit_code == 0
        assert "CrashLoopBackOff" in result.stdout

    def test_analyze_stdin(self, crashloop_log):
        result = runner.invoke(app, ["analyze", "-"], input=crashloop_log)
        assert result.exit_code == 0
        assert "CrashLoopBackOff" in result.stdout

    def test_analyze_no_match_exit_1(self, benign_text):
        result = runner.invoke(app, ["analyze", "-"], input=benign_text)
        assert result.exit_code == 1

    def test_analyze_missing_file_exit_2(self):
        result = runner.invoke(app, ["analyze", "/no/such/file.log"])
        assert result.exit_code == 2

    def test_analyze_json_is_valid(self, log_file):
        result = runner.invoke(app, ["analyze", str(log_file), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["technology"] == "kubernetes"
        assert "k8s.crashloopbackoff" in data["signatures_matched"]
        assert data["matched"] is True

    def test_analyze_tech_hint(self, log_file):
        result = runner.invoke(app, ["analyze", str(log_file), "--tech", "kubernetes"])
        assert result.exit_code == 0


class TestExplain:
    def test_explain_known(self):
        result = runner.invoke(app, ["explain", "CrashLoopBackOff"])
        assert result.exit_code == 0
        assert "CrashLoopBackOff" in result.stdout

    def test_explain_unknown_exit_1(self):
        result = runner.invoke(app, ["explain", "zzz-not-a-real-error-zzz"])
        assert result.exit_code == 1

    def test_explain_json(self):
        result = runner.invoke(app, ["explain", "CrashLoopBackOff", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["matched"] is True
        assert data["technology"] == "kubernetes"


class TestValidate:
    def test_validate_valid_terraform(self, tmp_path, valid_terraform):
        p = tmp_path / "main.tf"
        p.write_text(valid_terraform, encoding="utf-8")
        result = runner.invoke(app, ["validate", str(p)])
        assert result.exit_code == 0

    def test_validate_invalid_exit_1(self, tmp_path, unbalanced_terraform):
        p = tmp_path / "broken.tf"
        p.write_text(unbalanced_terraform, encoding="utf-8")
        result = runner.invoke(app, ["validate", str(p)])
        assert result.exit_code == 1

    def test_validate_json(self, tmp_path, valid_terraform):
        p = tmp_path / "main.tf"
        p.write_text(valid_terraform, encoding="utf-8")
        result = runner.invoke(app, ["validate", str(p), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["valid"] is True
        assert data["technology"] == "terraform"


class TestListAndVersion:
    def test_list(self):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "Knowledge Base" in result.stdout
        assert "k8s.crashloopbackoff" in result.stdout

    def test_list_filtered(self):
        result = runner.invoke(app, ["list", "--tech", "kubernetes"])
        assert result.exit_code == 0
        assert "k8s.crashloopbackoff" in result.stdout

    def test_version(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "devops-ai-toolkit" in result.stdout

    def test_no_args_shows_help(self):
        result = runner.invoke(app, [])
        # no_args_is_help -> exits 0 with help text.
        assert "analyze" in result.stdout
