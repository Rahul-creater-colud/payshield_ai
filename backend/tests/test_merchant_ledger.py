from __future__ import annotations

from app.config import settings


def _create_session(client, amount: float = 125.50) -> str:
    response = client.post(
        "/api/merchant/sessions",
        json={"merchant_id": "TEST_MERCHANT", "expected_amount": amount},
    )
    assert response.status_code == 201
    assert response.json()["simulated"] is True
    return response.json()["session_id"]


def test_merchant_ledger_callback_match_is_persisted_and_labeled(client):
    session_id = _create_session(client)
    response = client.post(
        f"/api/merchant/sessions/{session_id}/callbacks/simulate",
        json={"amount": 125.5, "status": "SUCCESS", "reference": "TEST-CALLBACK"},
    )

    assert response.status_code == 201
    assert response.json()["simulated"] is True
    assert "does not prove" in response.json()["disclaimer"]

    ledger = client.get(f"/api/merchant/sessions/{session_id}/ledger").json()
    assert ledger["ledger_status"] == "SIMULATED_AMOUNT_MATCH"
    assert ledger["callback"]["reference"] == "TEST-CALLBACK"
    assert ledger["callback"]["simulated"] is True


def test_merchant_ledger_mismatch_and_failed_callback_are_not_verified(client):
    mismatch_session = _create_session(client, 100)
    client.post(
        f"/api/merchant/sessions/{mismatch_session}/callbacks/simulate",
        json={"amount": 90, "status": "SUCCESS"},
    )
    mismatch = client.get(f"/api/merchant/sessions/{mismatch_session}/ledger").json()
    assert mismatch["ledger_status"] == "SIMULATED_AMOUNT_MISMATCH"

    failed_session = _create_session(client, 100)
    client.post(
        f"/api/merchant/sessions/{failed_session}/callbacks/simulate",
        json={"amount": 100, "status": "FAILED"},
    )
    failed = client.get(f"/api/merchant/sessions/{failed_session}/ledger").json()
    assert failed["ledger_status"] == "SIMULATED_FAILURE"


def test_simulated_callbacks_do_not_count_as_provider_blocks(client):
    before = client.get("/api/v1/fraud/analytics").json()["metrics"]["blockedTransactions"]
    session_id = _create_session(client)
    client.post(
        f"/api/merchant/sessions/{session_id}/callbacks/simulate",
        json={"amount": 125.5, "status": "SUCCESS"},
    )
    after = client.get("/api/v1/fraud/analytics").json()["metrics"]["blockedTransactions"]
    assert after == before


def test_merchant_ledger_rejects_invalid_input_and_unknown_sessions(client):
    assert client.post(
        "/api/merchant/sessions",
        json={"merchant_id": "TEST", "expected_amount": 0},
    ).status_code == 422
    assert client.get("/api/merchant/sessions/not-found/ledger").status_code == 404

    session_id = _create_session(client)
    invalid_callback = client.post(
        f"/api/merchant/sessions/{session_id}/callbacks/simulate",
        json={"amount": 125.5, "status": "PENDING"},
    )
    assert invalid_callback.status_code == 422


def test_simulated_callbacks_can_be_disabled(client, monkeypatch):
    session_id = _create_session(client)
    monkeypatch.setattr(settings, "ENABLE_SIMULATED_CALLBACKS", False)
    response = client.post(
        f"/api/merchant/sessions/{session_id}/callbacks/simulate",
        json={"amount": 125.5, "status": "SUCCESS"},
    )
    assert response.status_code == 403
