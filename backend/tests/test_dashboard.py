"""Tests for /api/dashboard/summary."""

from __future__ import annotations


def test_dashboard_summary_200(client):
    r = client.get("/api/dashboard/summary")
    assert r.status_code == 200


def test_dashboard_has_required_keys(client):
    body = client.get("/api/dashboard/summary").json()
    assert "totals" in body
    assert "risk_distribution" in body
    assert "recent_alerts" in body
    assert "grievance_summary" in body
    assert "suspicious_clusters" in body
    assert "data_label" in body
    assert "simulated" in body


def test_dashboard_data_label(client):
    body = client.get("/api/dashboard/summary").json()
    assert body["data_label"] == "LOCAL PROTOTYPE RECORDS (MAY INCLUDE SYNTHETIC SEED DATA)"


def test_dashboard_simulated_true(client):
    body = client.get("/api/dashboard/summary").json()
    assert body["simulated"] is True


def test_dashboard_totals_shape(client):
    body = client.get("/api/dashboard/summary").json()
    totals = body["totals"]
    assert "transactions" in totals
    assert "assessments" in totals
    assert "open_grievances" in totals
    assert totals["transactions"] >= 0
    assert totals["assessments"] >= 0


def test_dashboard_risk_distribution_shape(client):
    body = client.get("/api/dashboard/summary").json()
    dist = body["risk_distribution"]
    assert "LOW" in dist
    assert "MEDIUM" in dist
    assert "HIGH" in dist


def test_dashboard_grievance_summary_shape(client):
    body = client.get("/api/dashboard/summary").json()
    grv = body["grievance_summary"]
    for status in ["SUBMITTED", "UNDER_REVIEW", "MORE_INFO_REQUIRED", "RESOLVED", "REJECTED"]:
        assert status in grv


def test_dashboard_recent_alerts_shape(client):
    body = client.get("/api/dashboard/summary").json()
    for alert in body["recent_alerts"]:
        assert "assessment_id" in alert
        assert "transaction_id" in alert
        assert "score" in alert
        assert "category" in alert
        assert alert["category"] in ("MEDIUM", "HIGH")


def test_dashboard_counts_increase_after_assessment(client):
    before = client.get("/api/dashboard/summary").json()
    txn_before = before["totals"]["transactions"]
    asm_before = before["totals"]["assessments"]

    client.post("/api/risk/assess", json={
        "sender_id": "U001",
        "receiver_id": "ACC_101",
        "amount": 750.0,
        "request_type": "PAY",
        "context": {"unsolicited": False},
    })

    after = client.get("/api/dashboard/summary").json()
    assert after["totals"]["transactions"] > txn_before
    assert after["totals"]["assessments"] > asm_before


def test_dashboard_suspicious_clusters_list(client):
    body = client.get("/api/dashboard/summary").json()
    clusters = body["suspicious_clusters"]
    assert isinstance(clusters, list)
    # ACC_300 should appear as a suspicious cluster (fan-in from seed data)
    centers = [c["center"] for c in clusters]
    assert "ACC_300" in centers
