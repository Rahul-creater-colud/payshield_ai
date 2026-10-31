"""Tests for /health and /api/health."""

from __future__ import annotations


def test_health_root(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["service"] == "payshield-backend"
    assert body["db"] == "ok"
    assert "time" in body
    assert "version" in body
    assert body["ml_model"]["status"] in {"active", "disabled", "unavailable"}
    assert body["ml_model"]["affects_final_score"] is False


def test_health_api(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"
