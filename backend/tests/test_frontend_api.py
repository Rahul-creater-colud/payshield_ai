"""Tests for /api/v1 frontend integration endpoints."""

from __future__ import annotations


def test_api_v1_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert "version" in body
    assert "ai_model" in body
    assert "threat_db_records" in body


def test_api_v1_analyze_high_risk_collect(client):
    r = client.post(
        "/api/v1/fraud/analyze",
        json={
            "transaction_id": "UPI/2026/TEST-PHISH-01",
            "sender_upi": "vikram.sharma@okhdfcbank",
            "receiver_upi": "sbi-kyc-update-desk@ybl",
            "amount": 24999.0,
            "transaction_type": "COLLECT_REQUEST",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["status"] == "BLOCKED"
    assert data["riskCategory"] == "HIGH"
    assert data["riskScore"] >= 70
    assert len(data["reasons"]) > 0
    assert data["indicators"]["collectRequestAnomaly"] is True


def test_api_v1_analyze_safe_p2m(client):
    r = client.post(
        "/api/v1/fraud/analyze",
        json={
            "transaction_id": "UPI/2026/TEST-SAFE-01",
            "sender_upi": "sneha.reddy@okicici",
            "receiver_upi": "swiggy.pay@icici",
            "amount": 480.0,
            "transaction_type": "P2M",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["status"] == "SAFE"
    assert data["riskCategory"] == "LOW"
    assert data["riskScore"] <= 39


def test_api_v1_get_transactions(client):
    r = client.get("/api/v1/transactions")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert body["total"] >= 1


def test_api_v1_get_collect_requests(client):
    r = client.get("/api/v1/collect-requests")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert len(body["data"]) >= 4


def test_api_v1_action_collect_request(client):
    r = client.post(
        "/api/v1/collect-requests/col-201/action",
        json={"action": "REJECT"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["action"] == "REJECT"
    assert body["status"] == "REJECTED"


def test_api_v1_fraud_analytics(client):
    r = client.get("/api/v1/fraud/analytics")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert "metrics" in body
    assert "dailyActivity" in body
    assert "riskDistribution" in body
    assert body["metrics"]["totalTransactions"] > 0


def test_api_v1_screenshot_ocr_sample(client):
    r = client.post(
        "/api/v1/fraud/screenshot-ocr",
        data={"sample_key": "scan-sample-2"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["riskCategory"] == "HIGH"
    assert "extractedEntities" in data
    assert "forensicFindings" in data


def test_api_v1_fraud_alerts(client):
    r = client.get("/api/v1/fraud/alerts")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert "summary" in body
    assert len(body["data"]) >= 4


def test_api_v1_resolve_alert(client):
    r = client.post(
        "/api/v1/fraud/alerts/alt-501/resolve",
        json={"notes": "Beneficiary frozen by operations"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["status"] == "RESOLVED"

