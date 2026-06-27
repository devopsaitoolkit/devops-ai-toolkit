"""Tests for the FastAPI REST API via TestClient."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from devops_ai_toolkit.api.app import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


class TestMeta:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["signatures"] > 0
        assert "provider" in data
        assert isinstance(data["provider_available"], bool)

    def test_version(self, client):
        resp = client.get("/version")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "devops-ai-toolkit"
        assert data["version"]


class TestAnalyzeEndpoints:
    def test_analyze_log(self, client, crashloop_log):
        resp = client.post("/analyze/log", json={"content": crashloop_log})
        assert resp.status_code == 200
        data = resp.json()
        assert data["matched"] is True
        assert "k8s.crashloopbackoff" in data["signatures_matched"]
        assert data["technology"] == "kubernetes"
        assert "confidence_percent" in data

    def test_analyze_yaml(self, client, valid_k8s_manifest):
        resp = client.post("/analyze/yaml", json={"content": valid_k8s_manifest})
        assert resp.status_code == 200
        assert resp.json()["technology"] == "kubernetes"

    def test_analyze_terraform(self, client, terraform_state_lock_log):
        resp = client.post("/analyze/terraform", json={"content": terraform_state_lock_log})
        assert resp.status_code == 200
        data = resp.json()
        assert data["technology"] == "terraform"
        assert "terraform.state_lock" in data["signatures_matched"]

    def test_analyze_empty_content_rejected(self, client):
        resp = client.post("/analyze/log", json={"content": ""})
        assert resp.status_code == 422

    def test_analyze_max_root_causes(self, client, crashloop_log):
        resp = client.post("/analyze/log", json={"content": crashloop_log, "max_root_causes": 1})
        assert resp.status_code == 200
        assert len(resp.json()["root_causes"]) <= 1


class TestExplain:
    def test_explain_known(self, client):
        resp = client.post("/explain", json={"error": "CrashLoopBackOff"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["matched"] is True
        assert data["technology"] == "kubernetes"
        assert data["root_causes"]

    def test_explain_unknown(self, client):
        resp = client.post("/explain", json={"error": "zzz-unknown-zzz"})
        assert resp.status_code == 200
        assert resp.json()["matched"] is False


class TestValidate:
    def test_validate_terraform_ok(self, client, valid_terraform):
        resp = client.post("/validate", json={"content": valid_terraform})
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["technology"] == "terraform"

    def test_validate_bad_kubernetes(self, client, bad_k8s_manifest):
        resp = client.post("/validate", json={"content": bad_k8s_manifest})
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        assert data["issues"]
        assert "error_count" in data

    def test_validate_empty_rejected(self, client):
        resp = client.post("/validate", json={"content": ""})
        assert resp.status_code == 422
