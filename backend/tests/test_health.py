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


def test_frontend_development_origin_is_allowed(client):
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-client-platform,x-request-time",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_unconfigured_origin_is_not_allowed(client):
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
