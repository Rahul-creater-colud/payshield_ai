"""Persisted merchant-ledger demonstration routes.

All callbacks are locally simulated and must never be treated as provider
confirmation or proof that a real payment was received.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import AppError, ErrorCode
from app.models import MerchantSession, PaymentEvent
from app.services.audit_service import record_audit_event

router = APIRouter(tags=["merchant-demo"])


class MerchantSessionRequest(BaseModel):
    merchant_id: str = Field(..., min_length=1, max_length=128)
    expected_amount: float = Field(..., gt=0, le=1_000_000, allow_inf_nan=False)


class SimulatedCallbackRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    merchant_id: str = Field(..., min_length=1, max_length=128)
    amount: float = Field(..., gt=0, le=1_000_000, allow_inf_nan=False)
    status: Literal["SUCCESS", "FAILED"]
    provider_reference: Optional[str] = Field(default=None, max_length=128)


def _session_response(session: MerchantSession, events: list[PaymentEvent]) -> dict:
    return {
        "session_id": session.session_id,
        "merchant_id": session.merchant_id,
        "expected_amount": session.expected_amount,
        "status": session.status,
        "created_at": session.created_at,
        "status_history": [
            {
                "event_id": event.event_id,
                "status": event.status,
                "provider_reference": event.provider_reference,
                "simulated": event.simulated,
                "recorded_at": event.verified_at,
            }
            for event in events
        ],
        "simulated": True,
        "data_label": "DEMO DATA — simulated merchant ledger",
        "disclaimer": (
            "This local status is simulated, not a bank or payment-provider confirmation."
        ),
    }


@router.post("/api/merchant/sessions", status_code=201)
def create_merchant_session(
    request: MerchantSessionRequest,
    db: Session = Depends(get_db),
):
    session = MerchantSession(
        session_id=f"PS_{uuid.uuid4().hex.upper()}",
        merchant_id=request.merchant_id.strip(),
        expected_amount=request.expected_amount,
        created_at=datetime.now(timezone.utc).isoformat(),
        status="PENDING",
    )
    db.add(session)
    record_audit_event(
        db,
        entity_type="merchant_session",
        entity_id=session.session_id,
        action="created",
        details={"status": "PENDING", "simulated": True},
    )
    db.commit()
    db.refresh(session)
    return _session_response(session, [])


@router.get("/api/merchant/transactions/{reference}")
def get_merchant_transaction(reference: str, db: Session = Depends(get_db)):
    session = db.get(MerchantSession, reference)
    if session is None:
        raise AppError(ErrorCode.NOT_FOUND, "Merchant session not found.", 404)
    events = (
        db.query(PaymentEvent)
        .filter(PaymentEvent.session_id == session.session_id)
        .order_by(PaymentEvent.verified_at.asc(), PaymentEvent.event_id.asc())
        .all()
    )
    return _session_response(session, events)


@router.post("/api/payments/simulate-callback", status_code=201)
def simulate_payment_callback(
    request: SimulatedCallbackRequest,
    db: Session = Depends(get_db),
):
    session = db.get(MerchantSession, request.session_id)
    if session is None:
        raise AppError(ErrorCode.NOT_FOUND, "Merchant session not found.", 404)
    if session.status != "PENDING":
        raise AppError(
            ErrorCode.CONFLICT,
            "This session already has a terminal payment status.",
            409,
        )
    if session.merchant_id != request.merchant_id.strip():
        raise AppError(ErrorCode.BAD_REQUEST, "Merchant does not match the session.", 400)
    if abs(session.expected_amount - request.amount) > 0.000001:
        raise AppError(ErrorCode.BAD_REQUEST, "Amount does not match the session.", 400)
    if request.provider_reference:
        duplicate_reference = (
            db.query(PaymentEvent)
            .filter(PaymentEvent.provider_reference == request.provider_reference)
            .first()
        )
        if duplicate_reference:
            raise AppError(ErrorCode.CONFLICT, "Callback reference was already recorded.", 409)

    event = PaymentEvent(
        event_id=f"EV_{uuid.uuid4().hex.upper()}",
        session_id=session.session_id,
        provider_reference=request.provider_reference,
        status=request.status,
        simulated=True,
        verified_at=datetime.now(timezone.utc).isoformat(),
    )
    session.status = request.status
    db.add(event)
    record_audit_event(
        db,
        entity_type="merchant_session",
        entity_id=session.session_id,
        action="simulated_status_recorded",
        details={"status": request.status, "simulated": True},
    )
    db.commit()
    db.refresh(session)
    return _session_response(session, [event])