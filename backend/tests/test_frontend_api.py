"""Tests for /api/v1 frontend integration endpoints."""

from __future__ import annotations


def test_api_v1_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert "version" in body
    assert body["detection_engine"] == "rule-based heuristics"
    assert body["payment_provider_integration"] is False
    assert body["simulated"] is True
    assert body["data_label"] == "LOCAL PROTOTYPE RECORDS (MAY INCLUDE SYNTHETIC SEED DATA)"
    assert body["ml_model"]["status"] in {"active", "disabled", "unavailable"}
    assert body["ml_model"]["affects_final_score"] is False


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
    assert data["status"] == "STOP_RECOMMENDED"
    assert data["riskCategory"] == "HIGH"
    assert data["riskScore"] >= 70
    assert data["payment_executed"] is False
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
    assert body["data"] == []
    assert body["available"] is False


def test_api_v1_action_collect_request(client):
    r = client.post(
        "/api/v1/collect-requests/col-201/action",
        json={"action": "REJECT"},
    )
    assert r.status_code == 501
    assert "payment-provider integration" in r.json()["error"]["message"]


def test_api_v1_fraud_analytics(client):
    r = client.get("/api/v1/fraud/analytics")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert "metrics" in body
    assert "dailyActivity" in body
    assert "riskDistribution" in body
    assert body["metrics"]["totalTransactions"] == client.get("/api/v1/transactions").json()["total"]
    assert body["metrics"]["totalFraudPreventedAmount"] is None
    assert body["data_label"] == "LOCAL PROTOTYPE RECORDS (MAY INCLUDE SYNTHETIC SEED DATA)"


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
    assert body["total"] == len(body["data"])
    assert all(item["id"].startswith("ASM_") for item in body["data"])
    assert body["summary"]["fraudPreventedAmount"] is None


def test_api_v1_resolve_alert(client):
    alerts = client.get("/api/v1/fraud/alerts").json()["data"]
    assert alerts
    alert_id = alerts[0]["id"]
    r = client.post(
        f"/api/v1/fraud/alerts/{alert_id}/resolve",
        json={"notes": "Beneficiary frozen by operations"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["status"] == "RESOLVED"
    assert any(item["id"] == alert_id and item["status"] == "RESOLVED"
               for item in client.get("/api/v1/fraud/alerts").json()["data"])


def test_legacy_demo_endpoints_are_labeled_and_do_not_claim_blocked_payments(client):
    analytics = client.get("/api/v1/demo/fraud/analytics")
    assert analytics.status_code == 200
    analytics_body = analytics.json()
    assert analytics_body["data_label"].startswith("DEMO DATA")
    assert analytics_body["simulated"] is True
    assert analytics_body["metrics"]["blockedTransactions"] == 0
    assert analytics_body["metrics"]["totalFraudPreventedAmount"] is None
    assert all("fraudPrevented" not in item for item in analytics_body["dailyActivity"])

    transactions = client.get("/api/v1/demo/transactions")
    assert transactions.status_code == 200
    transaction_body = transactions.json()
    assert transaction_body["data_label"].startswith("DEMO DATA")
    assert transaction_body["simulated"] is True
    assert all(item["status"] != "BLOCKED" for item in transaction_body["data"])
