"""Tests for /api/catalog."""

from __future__ import annotations


def test_catalog_returns_200(client):
    r = client.get("/api/catalog")
    assert r.status_code == 200


def test_catalog_has_users(client):
    body = r = client.get("/api/catalog").json()
    assert len(body["users"]) >= 6
    assert all("user_id" in u and "display_name" in u for u in body["users"])


def test_catalog_has_accounts(client):
    body = client.get("/api/catalog").json()
    assert len(body["accounts"]) >= 10


def test_catalog_has_scenarios(client):
    body = client.get("/api/catalog").json()
    ids = {s["id"] for s in body["scenarios"]}
    assert {"A", "B", "C", "D", "LOW"} <= ids


def test_catalog_scenarios_have_valid_prefill(client):
    body = client.get("/api/catalog").json()
    for scenario in body["scenarios"]:
        pf = scenario["prefill"]
        assert "sender_id" in pf
        assert "receiver_id" in pf
        assert "amount" in pf
        assert pf["amount"] > 0
        assert pf["request_type"] in ("PAY", "COLLECT_REQUEST")


def test_catalog_simulated_true(client):
    body = client.get("/api/catalog").json()
    assert body["simulated"] is True


def test_catalog_request_types(client):
    body = client.get("/api/catalog").json()
    assert set(body["request_types"]) == {"PAY", "COLLECT_REQUEST"}
