from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.config import settings
from app.services.ml_model_service import (
    FEATURE_NAMES,
    ExperimentalMLModelService,
    build_transaction_features,
    ml_model_service,
)


class FakeModel:
    n_features_in_ = len(FEATURE_NAMES)
    feature_names_in_ = FEATURE_NAMES
    classes_ = [0, 1]

    def predict_proba(self, frame):
        assert tuple(frame.columns) == FEATURE_NAMES
        return [[0.25, 0.75]]


def test_build_features_uses_only_stored_history_before_assessment():
    assessed_at = datetime.fromisoformat("2026-02-02T04:30:00+05:30")
    history = [
        SimpleNamespace(
            transaction_id="old",
            timestamp=(assessed_at - timedelta(days=2)).isoformat(),
            amount=300.0,
            receiver_id="known@upi",
        ),
        SimpleNamespace(
            transaction_id="recent",
            timestamp=(assessed_at - timedelta(hours=20)).isoformat(),
            amount=100.0,
            receiver_id="known@upi",
        ),
        SimpleNamespace(
            transaction_id="future",
            timestamp=(assessed_at + timedelta(hours=1)).isoformat(),
            amount=900.0,
            receiver_id="new@upi",
        ),
    ]

    features, assumptions = build_transaction_features(
        amount=400.0,
        timestamp=assessed_at,
        previous_transactions=history,
        receiver_id="NEW@UPI",
    )

    assert features["transaction_hour"] == 4
    assert features["transaction_count_24h"] == 1
    assert features["is_new_receiver"] == 1
    assert features["avg_transaction_amount"] == 200.0
    assert features["amount_deviation"] == 1.0
    assert features["failed_attempts"] == 0
    assert any("Failed-attempt history is not stored" in item for item in assumptions)


def test_model_probability_uses_artifact_threshold(monkeypatch):
    monkeypatch.setattr(settings, "ML_MODEL_ENABLED", True)
    service = ExperimentalMLModelService()
    monkeypatch.setattr(service, "_load_artifacts", lambda: (FakeModel(), 0.6))

    result = service.predict({name: 1 for name in FEATURE_NAMES})

    assert result["status"] == "active"
    assert result["probability"] == 0.75
    assert result["threshold"] == 0.6
    assert result["prediction"] == "SUSPICIOUS"
    assert result["affects_final_score"] is False


def test_model_disabled_status_is_explicit(monkeypatch):
    monkeypatch.setattr(settings, "ML_MODEL_ENABLED", False)
    result = ExperimentalMLModelService().status()
    assert result["status"] == "disabled"
    assert "disabled" in result["message"].lower()


def test_missing_artifacts_report_unavailable(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "ML_MODEL_ENABLED", True)
    monkeypatch.setattr(settings, "ML_MODEL_DIR", str(tmp_path))

    result = ExperimentalMLModelService().status()

    assert result["status"] == "unavailable"
    assert "artifacts are missing" in result["message"]


def test_analyze_endpoint_returns_supplemental_model_estimate(client, monkeypatch):
    def predict(features, assumptions):
        return {
            "status": "active",
            "model_name": "Experimental Random Forest",
            "training_data": "Synthetic generated labels; not real UPI outcomes",
            "affects_final_score": False,
            "message": "Supplemental model estimate is available.",
            "probability": 0.99,
            "threshold": 0.6,
            "prediction": "SUSPICIOUS",
            "feature_assumptions": assumptions,
        }

    monkeypatch.setattr(ml_model_service, "predict", predict)
    response = client.post(
        "/api/v1/fraud/analyze",
        json={
            "transaction_id": "ML-ESTIMATE-TEST",
            "sender_upi": "ml-test-sender@upi",
            "receiver_upi": "ml-test-recipient@upi",
            "amount": 25.0,
            "transaction_time": datetime.now(timezone.utc).isoformat(),
            "transaction_type": "P2P",
        },
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["ml_model"]["probability"] == 0.99
    assert body["ml_model"]["affects_final_score"] is False
    assert body["riskCategory"] == "LOW"


def test_layered_risk_endpoint_returns_supplemental_model_estimate(
    client, low_risk_payload, monkeypatch
):
    def predict(features, assumptions):
        return {
            "status": "active",
            "model_name": "Experimental Random Forest",
            "training_data": "Synthetic generated labels; not real UPI outcomes",
            "affects_final_score": False,
            "message": "Supplemental model estimate is available.",
            "probability": 0.99,
            "threshold": 0.6,
            "prediction": "SUSPICIOUS",
            "feature_assumptions": assumptions,
        }

    monkeypatch.setattr(ml_model_service, "predict", predict)
    response = client.post("/api/risk/assess", json=low_risk_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["ml_model"]["probability"] == 0.99
    assert body["ml_model"]["affects_final_score"] is False
    assert body["category"] == "LOW"
