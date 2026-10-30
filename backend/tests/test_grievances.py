"""Tests for /api/grievances."""

from __future__ import annotations

import pytest


def _make_assessment(client):
    """Helper: run a risk assessment and return the assessment_id."""
    r = client.post("/api/risk/assess", json={
        "sender_id": "U001",
        "receiver_id": "ACC_101",
        "amount": 500.0,
        "request_type": "PAY",
        "context": {"unsolicited": False},
    })
    assert r.status_code == 200, r.text
    return r.json()["assessment_id"]


# ── Create ──────────────────────────────────────────────────────────────────

def test_create_grievance_201(client):
    asm_id = _make_assessment(client)
    r = client.post("/api/grievances", json={
        "user_reference": "U001",
        "assessment_id": asm_id,
        "reason": "I did not make this transaction",
    })
    assert r.status_code == 201


def test_create_grievance_returns_case_id(client):
    asm_id = _make_assessment(client)
    r = client.post("/api/grievances", json={
        "user_reference": "U001",
        "assessment_id": asm_id,
        "reason": "I did not authorize this payment at all",
    })
    body = r.json()
    assert body["case_id"].startswith("CASE_")
    assert body["status"] == "SUBMITTED"


def test_create_grievance_has_disclaimer(client):
    asm_id = _make_assessment(client)
    r = client.post("/api/grievances", json={
        "user_reference": "U001",
        "assessment_id": asm_id,
        "reason": "Unauthorized transaction on my account",
    })
    body = r.json()
    assert "disclaimer" in body


def test_create_grievance_status_history(client):
    asm_id = _make_assessment(client)
    r = client.post("/api/grievances", json={
        "user_reference": "U001",
        "assessment_id": asm_id,
        "reason": "This was flagged incorrectly by the system",
    })
    body = r.json()
    assert len(body["status_history"]) == 1
    assert body["status_history"][0]["status"] == "SUBMITTED"


def test_create_grievance_unknown_assessment_404(client):
    r = client.post("/api/grievances", json={
        "user_reference": "U001",
        "assessment_id": "ASM_NOTREAL",
        "reason": "This assessment does not exist here",
    })
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_create_grievance_short_reason_422(client):
    asm_id = _make_assessment(client)
    r = client.post("/api/grievances", json={
        "user_reference": "U001",
        "assessment_id": asm_id,
        "reason": "short",
    })
    assert r.status_code == 422


# ── GET single ──────────────────────────────────────────────────────────────

def test_get_grievance_by_id(client):
    asm_id = _make_assessment(client)
    create_r = client.post("/api/grievances", json={
        "user_reference": "U001",
        "assessment_id": asm_id,
        "reason": "Testing retrieval of a single grievance case",
    })
    case_id = create_r.json()["case_id"]
    r = client.get(f"/api/grievances/{case_id}")
    assert r.status_code == 200
    assert r.json()["case_id"] == case_id


def test_get_grievance_not_found(client):
    r = client.get("/api/grievances/CASE_DOESNOTEXIST")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


# ── List with filters ───────────────────────────────────────────────────────

def test_list_grievances(client):
    asm_id = _make_assessment(client)
    client.post("/api/grievances", json={
        "user_reference": "U002",
        "assessment_id": asm_id,
        "reason": "I did not initiate this payment transaction at all",
    })
    r = client.get("/api/grievances")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body
    assert "total" in body
    assert body["total"] >= 1


def test_list_grievances_filter_by_status(client):
    r = client.get("/api/grievances?status=SUBMITTED")
    assert r.status_code == 200
    body = r.json()
    for item in body["items"]:
        assert item["status"] == "SUBMITTED"


def test_list_grievances_filter_by_user(client):
    asm_id = _make_assessment(client)
    client.post("/api/grievances", json={
        "user_reference": "U_FILTER_TEST",
        "assessment_id": asm_id,
        "reason": "Testing filter by user reference in grievance list",
    })
    r = client.get("/api/grievances?user_reference=U_FILTER_TEST")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    for item in body["items"]:
        assert item["user_reference"] == "U_FILTER_TEST"


# ── PATCH ───────────────────────────────────────────────────────────────────

def test_patch_grievance_requires_reviewer_note(client):
    asm_id = _make_assessment(client)
    create_r = client.post("/api/grievances", json={
        "user_reference": "U001",
        "assessment_id": asm_id,
        "reason": "Testing patch requires reviewer note to be present",
    })
    case_id = create_r.json()["case_id"]
    # Missing reviewer_note
    r = client.patch(f"/api/grievances/{case_id}", json={"status": "UNDER_REVIEW"})
    assert r.status_code == 422


def test_patch_grievance_success(client):
    asm_id = _make_assessment(client)
    create_r = client.post("/api/grievances", json={
        "user_reference": "U001",
        "assessment_id": asm_id,
        "reason": "Testing that patch with reviewer note succeeds correctly",
    })
    case_id = create_r.json()["case_id"]
    r = client.patch(f"/api/grievances/{case_id}", json={
        "status": "UNDER_REVIEW",
        "reviewer_note": "Case being investigated",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "UNDER_REVIEW"
    assert body["reviewer_note"] == "Case being investigated"


def test_patch_grievance_history_appended(client):
    asm_id = _make_assessment(client)
    create_r = client.post("/api/grievances", json={
        "user_reference": "U001",
        "assessment_id": asm_id,
        "reason": "Testing that status history is appended on each update",
    })
    case_id = create_r.json()["case_id"]
    client.patch(f"/api/grievances/{case_id}", json={
        "status": "UNDER_REVIEW",
        "reviewer_note": "Step 1",
    })
    r = client.patch(f"/api/grievances/{case_id}", json={
        "status": "MORE_INFO_REQUIRED",
        "reviewer_note": "Step 2 – need more info",
    })
    body = r.json()
    assert len(body["status_history"]) == 3  # SUBMITTED + UNDER_REVIEW + MORE_INFO_REQUIRED


def test_patch_terminal_state_rejected(client):
    asm_id = _make_assessment(client)
    create_r = client.post("/api/grievances", json={
        "user_reference": "U001",
        "assessment_id": asm_id,
        "reason": "Testing that resolved grievance cannot be updated further",
    })
    case_id = create_r.json()["case_id"]
    client.patch(f"/api/grievances/{case_id}", json={
        "status": "RESOLVED",
        "reviewer_note": "Closing case",
    })
    # Now try to update again – should fail
    r = client.patch(f"/api/grievances/{case_id}", json={
        "status": "UNDER_REVIEW",
        "reviewer_note": "Should not work",
    })
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "BAD_REQUEST"


def test_patch_cannot_set_submitted(client):
    asm_id = _make_assessment(client)
    create_r = client.post("/api/grievances", json={
        "user_reference": "U001",
        "assessment_id": asm_id,
        "reason": "Testing that SUBMITTED is not a valid patch target status",
    })
    case_id = create_r.json()["case_id"]
    r = client.patch(f"/api/grievances/{case_id}", json={
        "status": "SUBMITTED",
        "reviewer_note": "Try to reset",
    })
    assert r.status_code == 422  # validator rejects it
