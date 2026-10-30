"""Catalog router – frontend dropdowns and scenario prefills."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DemoUser, AccountOrVPA

router = APIRouter(prefix="/api", tags=["catalog"])

SCENARIOS = [
    {
        "id": "A",
        "title": "Fake Collect Request (Refund Scam)",
        "description": (
            "Scammer sends a collect request posing as a refund. "
            "Approving it debits your account, not credits it."
        ),
        "prefill": {
            "sender_id": "U001",
            "receiver_id": "ACC_150",
            "amount": 2999.0,
            "request_type": "COLLECT_REQUEST",
            "context": {
                "message_text": "You have received a refund, approve to receive your money",
                "unsolicited": True,
                "events": ["refund_message", "link_click", "collect_request"],
            },
        },
    },
    {
        "id": "B",
        "title": "Mule Network (Fan-in / Fan-out)",
        "description": (
            "Multiple senders funnel funds to ACC_300, which rapidly "
            "forwards to ACC_401/402/403. Classic money-mule pattern."
        ),
        "prefill": {
            "sender_id": "U003",
            "receiver_id": "ACC_300",
            "amount": 9500.0,
            "request_type": "PAY",
            "context": {"unsolicited": False},
        },
    },
    {
        "id": "C",
        "title": "Fake Screenshot (Merchant Session)",
        "description": (
            "A pending merchant session (SESS_001) has no matching payment event – "
            "a fraudster may show a fake screenshot of payment."
        ),
        "prefill": {
            "sender_id": "U006",
            "receiver_id": "ACC_500",
            "amount": 1500.0,
            "request_type": "PAY",
            "context": {"unsolicited": False},
        },
    },
    {
        "id": "D",
        "title": "Genuine User, New Recipient",
        "description": (
            "Normal amount to a new but clean recipient. "
            "Should score MEDIUM at most, never HIGH."
        ),
        "prefill": {
            "sender_id": "U001",
            "receiver_id": "ACC_111",
            "amount": 1000.0,
            "request_type": "PAY",
            "context": {"unsolicited": False},
        },
    },
    {
        "id": "LOW",
        "title": "Low-Risk (Familiar Recipient)",
        "description": "Familiar recipient, usual amount, usual hour – should be LOW.",
        "prefill": {
            "sender_id": "U001",
            "receiver_id": "ACC_101",
            "amount": 500.0,
            "request_type": "PAY",
            "context": {"unsolicited": False},
        },
    },
]


@router.get("/catalog")
def get_catalog(db: Session = Depends(get_db)):
    users = [
        {"user_id": u.user_id, "display_name": u.display_name}
        for u in db.query(DemoUser).all()
    ]
    accounts = [
        {
            "account_id": a.account_id,
            "vpa": a.vpa,
            "label": a.vpa or a.account_id,
        }
        for a in db.query(AccountOrVPA).all()
    ]
    return {
        "users": users,
        "accounts": accounts,
        "request_types": ["PAY", "COLLECT_REQUEST"],
        "scenarios": SCENARIOS,
        "grievance_statuses": [
            "SUBMITTED", "UNDER_REVIEW", "MORE_INFO_REQUIRED", "RESOLVED", "REJECTED"
        ],
        "indicator_types": ["VPA", "MOBILE", "URL", "DOMAIN"],
        "simulated": True,
    }
