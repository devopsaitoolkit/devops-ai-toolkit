"""Tests for the REST plugin endpoints.

The API engine is a module-level lru_cached singleton, so plugin enable/disable
state persists across requests within this module. Assertions are ordered so the
suite leaves every plugin enabled at the end.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from devops_ai_toolkit.api.app import app

client = TestClient(app)


def test_list_plugins() -> None:
    resp = client.get("/plugins")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 20
    names = {p["name"] for p in data}
    assert "kubernetes" in names
    assert "docker" in names
    for p in data:
        assert {"name", "version", "source", "enabled", "technologies"} <= set(p)


def test_get_plugin_known() -> None:
    resp = client.get("/plugins/kubernetes")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "kubernetes"
    assert "supported_technologies" in data


def test_get_plugin_unknown() -> None:
    resp = client.get("/plugins/no-such-plugin")
    assert resp.status_code == 404
    assert "Unknown plugin" in resp.json()["detail"]


def test_disable_then_enable_redis() -> None:
    try:
        disable = client.post("/plugins/disable", json={"name": "redis"})
        assert disable.status_code == 200
        assert disable.json() == {"name": "redis", "enabled": False}

        listed = client.get("/plugins").json()
        redis = next(p for p in listed if p["name"] == "redis")
        assert redis["enabled"] is False
    finally:
        enable = client.post("/plugins/enable", json={"name": "redis"})
        assert enable.status_code == 200
        assert enable.json() == {"name": "redis", "enabled": True}

    listed = client.get("/plugins").json()
    redis = next(p for p in listed if p["name"] == "redis")
    assert redis["enabled"] is True


def test_toggle_unknown_returns_404() -> None:
    resp = client.post("/plugins/disable", json={"name": "no-such-plugin"})
    assert resp.status_code == 404
