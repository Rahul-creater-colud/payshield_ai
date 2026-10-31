from __future__ import annotations

import uuid

from app.models import AuditEvent
from tests.conftest import _TestingSessionLocal


def _create_session(client, amount=525.5):
    merchant_id = f"DEMO-MERCHANT-{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/api/merchant/sessions",
        json={"merchant_id": merchant_id, "expected_amount": amount},
    )
    assert response.status_code == 201, response.text
    return merchant_id, response.json()


def test_create_and_lookup_persisted_demo_session(client):
    merchant_id, created = _create_session(client)

    assert created["status"] == "PENDING"
    assert created["merchant_id"] == merchant_id
    assert created["simulated"] is True
    assert "DEMO DATA" in created["data_label"]
    looked_up = client.get(
        f"/api/merchant/transactions/{created['session_id']}"
    )
    assert looked_up.status_code == 200
    assert looked_up.json()["session_id"] == created["session_id"]
    assert looked_up.json()["status_history"] == []
    db = _TestingSessionLocal()
    try:
        audit = (
            db.query(AuditEvent)
            .filter(
                AuditEvent.entity_type == "merchant_session",
                AuditEvent.entity_id == created["session_id"],
            )
            .one()
        )
        assert audit.action == "created"
        assert audit.details == {"status": "PENDING", "simulated": True}
    finally:
        db.close()


def test_simulated_callback_checks_session_merchant_and_amount(client):
    merchant_id, session = _create_session(client)
    endpoint = "/api/payments/simulate-callback"
    base_payload = {
        "session_id": session["session_id"],
        "merchant_id": merchant_id,
        "amount": session["expected_amount"],
        "status": "SUCCESS",
    }

    wrong_merchant = client.post(
        endpoint, json={**base_payload, "merchant_id": "OTHER-MERCHANT"}
    )
    assert wrong_merchant.status_code == 400
    wrong_amount = client.post(
        endpoint, json={**base_payload, "amount": session["expected_amount"] + 1}
    )
    assert wrong_amount.status_code == 400

    assert client.get(
        f"/api/merchant/transactions/{session['session_id']}"
    ).json()["status"] == "PENDING"


def test_simulated_success_callback_is_audited_and_duplicate_rejected(client):
    merchant_id, session = _create_session(client)
    payload = {
        "session_id": session["session_id"],
        "merchant_id": merchant_id,
        "amount": session["expected_amount"],
        "status": "SUCCESS",
        "provider_reference": f"DEMO-REF-{uuid.uuid4().hex}",
    }
    callback = client.post("/api/payments/simulate-callback", json=payload)

    assert callback.status_code == 201
    body = callback.json()
    assert body["status"] == "SUCCESS"
    assert body["simulated"] is True
    assert len(body["status_history"]) == 1
    assert body["status_history"][0]["simulated"] is True

    lookup = client.get(f"/api/merchant/transactions/{session['session_id']}")
    assert lookup.status_code == 200
    assert lookup.json()["status_history"][0]["event_id"] == body["status_history"][0]["event_id"]

    duplicate = client.post("/api/payments/simulate-callback", json=payload)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "CONFLICT"


def test_duplicate_callback_reference_rejected_across_sessions(client):
    reference = f"DEMO-REF-{uuid.uuid4().hex}"
    sessions = [_create_session(client) for _ in range(2)]

    first_merchant, first_session = sessions[0]
    first = client.post(
        "/api/payments/simulate-callback",
        json={
            "session_id": first_session["session_id"],
            "merchant_id": first_merchant,
            "amount": first_session["expected_amount"],
            "status": "FAILED",
            "provider_reference": reference,
        },
    )
    assert first.status_code == 201

    second_merchant, second_session = sessions[1]
    duplicate = client.post(
        "/api/payments/simulate-callback",
        json={
            "session_id": second_session["session_id"],
            "merchant_id": second_merchant,
            "amount": second_session["expected_amount"],
            "status": "SUCCESS",
            "provider_reference": reference,
        },
    )
    assert duplicate.status_code == 409


def test_invalid_and_unknown_callback_requests_return_errors(client):
    missing_session = client.post(
        "/api/payments/simulate-callback",
        json={
            "session_id": "NO-SUCH-SESSION",
            "merchant_id": "DEMO",
            "amount": 1,
            "status": "SUCCESS",
        },
    )
    assert missing_session.status_code == 404

    invalid_status = client.post(
        "/api/payments/simulate-callback",
        json={
            "session_id": "NO-SUCH-SESSION",
            "merchant_id": "DEMO",
            "amount": 1,
            "status": "BLOCKED",
        },
    )
    assert invalid_status.status_code == 422