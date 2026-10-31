from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.main import create_app


@pytest.fixture
def empty_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_sessions = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db():
        db = test_sessions()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_empty_database_returns_zeroes_and_no_sample_rows(empty_client):
    analytics = empty_client.get("/api/v1/fraud/analytics").json()
    metrics = analytics["metrics"]
    assert metrics["totalTransactions"] == 0
    assert metrics["safeTransactions"] == 0
    assert metrics["suspiciousTransactions"] == 0
    assert metrics["blockedTransactions"] == 0
    assert metrics["stopReviewRecommendations"] == 0
    assert metrics["totalFraudPreventedAmount"] is None
    assert metrics["suspiciousAssessmentRatePercent"] is None
    assert analytics["dailyActivity"] == []
    assert sum(item["count"] for item in analytics["riskDistribution"]) == 0

    transactions = empty_client.get("/api/v1/transactions").json()
    alerts = empty_client.get("/api/v1/fraud/alerts").json()
    assert transactions == {
        "success": True,
        "total": 0,
        "data": [],
        "data_label": "DEMO / SYNTHETIC DATA",
        "simulated": True,
    }
    assert alerts["total"] == 0
    assert alerts["data"] == []


def test_unassessed_imported_statuses_do_not_become_risk_decisions(empty_client):
    session_generator = empty_client.app.dependency_overrides[get_db]()
    db = next(session_generator)
    try:
        for transaction_id, status in (
            ("IMPORTED-SAFE", "SAFE"),
            ("IMPORTED-FLAGGED", "FLAGGED"),
            ("IMPORTED-SUSPICIOUS", "SUSPICIOUS"),
        ):
            db.add(models.Transaction(
                transaction_id=transaction_id,
                sender_id="synthetic-sender@upi",
                receiver_id="synthetic-recipient@upi",
                amount=100,
                timestamp="2026-01-01T12:00:00+00:00",
                status=status,
                request_type="PAY",
            ))
        db.commit()
    finally:
        session_generator.close()

    transactions = empty_client.get("/api/v1/transactions").json()
    assert transactions["total"] == 3
    assert all(item["status"] == "UNASSESSED" for item in transactions["data"])
    assert all(item["riskCategory"] == "UNASSESSED" for item in transactions["data"])
    assert all(item["riskScore"] is None for item in transactions["data"])

    analytics = empty_client.get("/api/v1/fraud/analytics").json()
    metrics = analytics["metrics"]
    assert metrics["totalTransactions"] == 3
    assert metrics["assessedTransactions"] == 0
    assert metrics["safeTransactions"] == 0
    assert metrics["suspiciousTransactions"] == 0
    assert metrics["fraudRatePercent"] is None
    assert metrics["safeRatePercent"] is None
    assert metrics["suspiciousAssessmentRatePercent"] is None
    assert analytics["dailyActivity"] == []
    assert sum(item["count"] for item in analytics["riskDistribution"]) == 0

    legacy_transactions = empty_client.get("/api/v1/demo/transactions").json()
    assert legacy_transactions["total"] == 3
    assert all(item["status"] == "UNASSESSED" for item in legacy_transactions["data"])
    legacy_analytics = empty_client.get("/api/v1/demo/fraud/analytics").json()
    assert legacy_analytics["metrics"]["totalTransactions"] == 3
    assert legacy_analytics["metrics"]["assessedTransactions"] == 0


def test_legacy_demo_routes_do_not_fabricate_transactions(empty_client):
    transactions = empty_client.get("/api/v1/demo/transactions").json()
    assert transactions["total"] == 0
    assert transactions["data"] == []
    assert transactions["data_label"] == "DEMO / SYNTHETIC DATA"

    analytics = empty_client.get("/api/v1/demo/fraud/analytics").json()
    assert analytics["metrics"]["totalTransactions"] == 0
    assert analytics["metrics"]["fraudRatePercent"] is None
    assert analytics["dailyActivity"] == []

    missing = empty_client.get("/api/v1/demo/transactions/not-stored")
    assert missing.status_code == 404


def test_dashboard_and_transaction_records_use_same_persisted_rows(empty_client):
    high = empty_client.post(
        "/api/v1/fraud/analyze",
        json={
            "transaction_id": "TEST-DEMO-HIGH-01",
            "sender_upi": "sender@example",
            "receiver_upi": "refund-support@example",
            "amount": 500,
            "transaction_type": "P2P",
        },
    )
    safe = empty_client.post(
        "/api/v1/fraud/analyze",
        json={
            "transaction_id": "TEST-DEMO-SAFE-01",
            "sender_upi": "sender@example",
            "receiver_upi": "merchant@example",
            "amount": 100,
            "transaction_type": "P2M",
        },
    )
    assert high.status_code == safe.status_code == 200
    assert high.json()["data"]["status"] == "STOP_RECOMMENDED"
    assert high.json()["data"]["payment_executed"] is False
    assert safe.json()["data"]["status"] == "SAFE"

    records = empty_client.get("/api/v1/transactions").json()
    analytics = empty_client.get("/api/v1/fraud/analytics").json()
    assert records["total"] == len(records["data"]) == 2
    assert analytics["metrics"]["totalTransactions"] == records["total"]
    assert analytics["metrics"]["safeTransactions"] == 1
    assert analytics["metrics"]["suspiciousTransactions"] == 1
    assert analytics["metrics"]["stopReviewRecommendations"] == 1
    assert analytics["metrics"]["blockedTransactions"] == 0
    assert analytics["metrics"]["fraudRatePercent"] is None
    assert analytics["metrics"]["suspiciousAssessmentRatePercent"] == 50
    assert analytics["metrics"]["lowRiskAssessmentRatePercent"] == 50
    assert sum(item["count"] for item in analytics["riskDistribution"]) == 2
    assert empty_client.get("/api/v1/fraud/alerts").json()["total"] == 1


def test_missing_transaction_detail_is_not_replaced_with_sample(empty_client):
    response = empty_client.get("/api/v1/transactions/does-not-exist")
    assert response.status_code == 404
