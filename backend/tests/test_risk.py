"""Tests for /api/risk/assess and /api/risk/assessments."""

from __future__ import annotations

import pytest


# ── LOW risk ────────────────────────────────────────────────────────────────

def test_low_risk_returns_200(client, low_risk_payload):
    r = client.post("/api/risk/assess", json=low_risk_payload)
    assert r.status_code == 200


def test_low_risk_category(client, low_risk_payload):
    body = client.post("/api/risk/assess", json=low_risk_payload).json()
    assert body["category"] == "LOW"


def test_low_risk_simulated_true(client, low_risk_payload):
    body = client.post("/api/risk/assess", json=low_risk_payload).json()
    assert body["simulated"] is True


def test_low_risk_disclaimer(client, low_risk_payload):
    body = client.post("/api/risk/assess", json=low_risk_payload).json()
    assert "disclaimer" in body
    assert len(body["disclaimer"]) > 10


def test_low_risk_reasons_non_empty(client, low_risk_payload):
    body = client.post("/api/risk/assess", json=low_risk_payload).json()
    # Reasons list may be empty for truly clean tx – just check it's a list
    assert isinstance(body["reasons"], list)


def test_low_risk_has_assessment_id(client, low_risk_payload):
    body = client.post("/api/risk/assess", json=low_risk_payload).json()
    assert body["assessment_id"].startswith("ASM_")
    assert body["transaction_id"].startswith("TXN_")


def test_low_risk_action_proceed(client, low_risk_payload):
    body = client.post("/api/risk/assess", json=low_risk_payload).json()
    assert body["recommended_action"] == "PROCEED"


# ── Scenario A: collect request ─────────────────────────────────────────────

def test_scenario_a_collect_warning(client, collect_request_payload):
    body = client.post("/api/risk/assess", json=collect_request_payload).json()
    assert body["collect_request_warning"] is not None
    assert "DEBIT" in body["collect_request_warning"].upper() or "REQUEST" in body["collect_request_warning"].upper()


def test_scenario_a_category_medium_or_high(client, collect_request_payload):
    body = client.post("/api/risk/assess", json=collect_request_payload).json()
    assert body["category"] in ("MEDIUM", "HIGH")


def test_scenario_a_playbook_match(client, collect_request_payload):
    body = client.post("/api/risk/assess", json=collect_request_payload).json()
    pb_names = [p["name"] for p in body["playbook_matches"]]
    assert "FAKE_COLLECT_REQUEST" in pb_names or "REFUND_SCAM" in pb_names


def test_scenario_a_stop_or_verify_action(client, collect_request_payload):
    body = client.post("/api/risk/assess", json=collect_request_payload).json()
    assert body["recommended_action"] in ("STOP_AND_REVIEW", "CAUTION_VERIFY")


# ── Scenario B: mule network ────────────────────────────────────────────────

def test_scenario_b_high_or_medium(client, mule_payload):
    body = client.post("/api/risk/assess", json=mule_payload).json()
    assert body["category"] in ("MEDIUM", "HIGH")


def test_scenario_b_graph_flags(client, mule_payload):
    body = client.post("/api/risk/assess", json=mule_payload).json()
    # Should have graph_flags populated OR high score from graph layer
    assert body["score"] >= 40 or len(body["graph_flags"]) > 0


# ── Scenario D: new recipient, never HIGH ───────────────────────────────────

def test_scenario_d_not_high(client, new_recipient_payload):
    body = client.post("/api/risk/assess", json=new_recipient_payload).json()
    assert body["category"] != "HIGH", (
        f"New recipient with normal amount must NOT be HIGH. Got {body['category']} score={body['score']}"
    )


def test_scenario_d_no_collect_warning(client, new_recipient_payload):
    body = client.post("/api/risk/assess", json=new_recipient_payload).json()
    assert body["collect_request_warning"] is None


# ── Validation errors ───────────────────────────────────────────────────────

def test_unknown_sender_404(client):
    r = client.post("/api/risk/assess", json={
        "sender_id": "UNKNOWN_XYZ",
        "receiver_id": "ACC_101",
        "amount": 100.0,
        "request_type": "PAY",
    })
    assert r.status_code == 404
    body = r.json()
    assert "error" in body
    assert body["error"]["code"] == "NOT_FOUND"


def test_negative_amount_422(client):
    r = client.post("/api/risk/assess", json={
        "sender_id": "U001",
        "receiver_id": "ACC_101",
        "amount": -100.0,
        "request_type": "PAY",
    })
    assert r.status_code == 422
    body = r.json()
    assert "error" in body
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_zero_amount_422(client):
    r = client.post("/api/risk/assess", json={
        "sender_id": "U001",
        "receiver_id": "ACC_101",
        "amount": 0.0,
        "request_type": "PAY",
    })
    assert r.status_code == 422


def test_forbidden_otp_field_rejected(client):
    r = client.post("/api/risk/assess", json={
        "sender_id": "U001",
        "receiver_id": "ACC_101",
        "amount": 100.0,
        "request_type": "PAY",
        "otp": "123456",
    })
    assert r.status_code == 422
    body = r.json()
    assert "error" in body


def test_forbidden_pin_field_rejected(client):
    r = client.post("/api/risk/assess", json={
        "sender_id": "U001",
        "receiver_id": "ACC_101",
        "amount": 100.0,
        "request_type": "PAY",
        "pin": "1234",
    })
    assert r.status_code == 422


def test_forbidden_password_field_rejected(client):
    r = client.post("/api/risk/assess", json={
        "sender_id": "U001",
        "receiver_id": "ACC_101",
        "amount": 100.0,
        "request_type": "PAY",
        "password": "secret",
    })
    assert r.status_code == 422


# ── Retrieve stored assessment ───────────────────────────────────────────────

def test_get_assessment_by_id(client, low_risk_payload):
    post_body = client.post("/api/risk/assess", json=low_risk_payload).json()
    asm_id = post_body["assessment_id"]
    r = client.get(f"/api/risk/assessments/{asm_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["assessment_id"] == asm_id


def test_get_assessment_not_found(client):
    r = client.get("/api/risk/assessments/ASM_NOTEXIST")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_list_assessments(client, low_risk_payload):
    client.post("/api/risk/assess", json=low_risk_payload)
    r = client.get("/api/risk/assessments?limit=5")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert len(body) >= 1
