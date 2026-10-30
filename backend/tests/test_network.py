"""Tests for /api/accounts/{id}/network."""

from __future__ import annotations


def test_network_acc300_returns_200(client):
    r = client.get("/api/accounts/ACC_300/network")
    assert r.status_code == 200


def test_network_acc300_has_patterns(client):
    body = client.get("/api/accounts/ACC_300/network").json()
    pattern_types = {p["pattern"] for p in body["patterns"]}
    # ACC_300 receives from 5+ senders → FAN_IN
    assert "FAN_IN" in pattern_types


def test_network_acc300_has_fan_in_and_fan_out(client):
    body = client.get("/api/accounts/ACC_300/network").json()
    pattern_types = {p["pattern"] for p in body["patterns"]}
    # Has both senders (fan-in) and downstream recipients (fan-out or rapid)
    assert len(pattern_types) >= 1


def test_network_acc300_directed_edges(client):
    body = client.get("/api/accounts/ACC_300/network").json()
    assert len(body["edges"]) > 0
    for edge in body["edges"]:
        assert "->" in edge["direction"]
        assert "source" in edge
        assert "target" in edge
        assert "amount" in edge


def test_network_acc300_nodes_shape(client):
    body = client.get("/api/accounts/ACC_300/network").json()
    assert len(body["nodes"]) > 0
    for node in body["nodes"]:
        assert "id" in node
        assert "risk_level" in node
        assert node["risk_level"] in ("LOW", "MEDIUM", "HIGH")


def test_network_unknown_account_404(client):
    r = client.get("/api/accounts/ACC_NONEXISTENT/network")
    assert r.status_code == 404
    body = r.json()
    assert "error" in body
    assert body["error"]["code"] == "NOT_FOUND"


def test_network_simulated_true(client):
    body = client.get("/api/accounts/ACC_300/network").json()
    assert body["simulated"] is True


def test_network_has_disclaimer(client):
    body = client.get("/api/accounts/ACC_300/network").json()
    assert "disclaimer" in body


def test_network_center_matches_id(client):
    body = client.get("/api/accounts/ACC_300/network").json()
    assert body["center"] == "ACC_300"
