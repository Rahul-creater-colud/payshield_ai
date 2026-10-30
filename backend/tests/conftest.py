"""Shared pytest fixtures for PayShield AI tests."""

from __future__ import annotations

import json
import os
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import create_app
from app.db.seed import load_seed

# ── In-memory test DB ──────────────────────────────────────────────────────
TEST_DB_URL = "sqlite:///./test_payshield.db"

_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
_TestingSessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


def override_get_db():
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create tables and seed once per test session."""
    from app import models  # noqa: F401
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    db = _TestingSessionLocal()
    try:
        load_seed(db=db, seed_path="app/data/seed.json")
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=_engine)
    # Clean up file
    if os.path.exists("test_payshield.db"):
        try:
            os.remove("test_payshield.db")
        except Exception:
            pass


@pytest.fixture(scope="session")
def client(setup_test_db):
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ── Payload fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def low_risk_payload():
    """Scenario: familiar recipient, usual amount, usual hour → LOW."""
    return {
        "sender_id": "U001",
        "receiver_id": "ACC_101",
        "amount": 500.0,
        "request_type": "PAY",
        "context": {"unsolicited": False},
    }


@pytest.fixture
def collect_request_payload():
    """Scenario A: fake collect request from REPORTED VPA."""
    return {
        "sender_id": "U001",
        "receiver_id": "ACC_150",
        "amount": 2999.0,
        "request_type": "COLLECT_REQUEST",
        "context": {
            "message_text": "You have received a refund, approve to receive",
            "unsolicited": True,
            "events": ["refund_message", "link_click", "collect_request"],
        },
    }


@pytest.fixture
def mule_payload():
    """Scenario B: sending to the mule hub ACC_300."""
    return {
        "sender_id": "U003",
        "receiver_id": "ACC_300",
        "amount": 9500.0,
        "request_type": "PAY",
        "context": {"unsolicited": False},
    }


@pytest.fixture
def new_recipient_payload():
    """Scenario D: genuine user, new but clean recipient → MEDIUM at most."""
    return {
        "sender_id": "U001",
        "receiver_id": "ACC_111",
        "amount": 1000.0,
        "request_type": "PAY",
        "context": {"unsolicited": False},
    }
