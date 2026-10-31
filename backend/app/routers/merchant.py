"""Local merchant ledger and explicitly simulated payment callbacks."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.errors import AppError, ErrorCode
from app.models import MerchantSession, PaymentEvent, SimulatedPaymentCallback
from app.schemas import MerchantSessionCreateRequest, SimulatedPaymentCallbackRequest

router = APIRouter(prefix="/api/merchant", tags=["merchant-ledger"])
DISCLAIMER = (
    "Local simulated ledger only. This record is not a bank or payment-provider "
    "confirmation and does not prove that money moved."
)


def _session_response(session: MerchantSession) -> dict:
    return {
        "session_id": session.session_id,
        "merchant_id": session.merchant_id,
        "expected_amount": session.expected_amount,
        "status": session.status,
        "created_at": session.created_at,
        "simulated": True,
        "disclaimer": DISCLAIMER,
    }


def _get_session(db: Session, session_id: str) -> MerchantSession:
    session = db.get(MerchantSession, session_id)
    if session is None:
        raise AppError(ErrorCode.NOT_FOUND, f"Merchant session {session_id} not found.", 404)
    return session


@router.post("/sessions", status_code=201)
def create_session(
    request: MerchantSessionCreateRequest,
    db: Session = Depends(get_db),
):
    session = MerchantSession(
        session_id=f"SESS_{uuid.uuid4().hex[:12].upper()}",
        merchant_id=request.merchant_id.strip(),
        expected_amount=round(request.expected_amount, 2),
        created_at=datetime.now(timezone.utc).isoformat(),
        status="PENDING",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return _session_response(session)


@router.post("/sessions/{session_id}/callbacks/simulate", status_code=201)
def simulate_payment_callback(
    session_id: str,
    request: SimulatedPaymentCallbackRequest,
    db: Session = Depends(get_db),
):
    if not settings.ENABLE_SIMULATED_CALLBACKS:
        raise AppError(
            ErrorCode.BAD_REQUEST,
            "Simulated callbacks are disabled by configuration.",
            403,
        )
    session = _get_session(db, session_id)
    verified_provider_event = (
        db.query(PaymentEvent)
        .filter(
            PaymentEvent.session_id == session_id,
            PaymentEvent.status == "SUCCESS",
            PaymentEvent.simulated.is_(False),
            PaymentEvent.verified_at.is_not(None),
            PaymentEvent.provider_reference.is_not(None),
        )
        .first()
    )
    if verified_provider_event:
        raise AppError(
            ErrorCode.CONFLICT,
            "A verified provider event already exists; a simulated callback cannot replace it.",
            409,
        )

    callback = SimulatedPaymentCallback(
        callback_id=f"SIM_{uuid.uuid4().hex[:12].upper()}",
        session_id=session_id,
        amount=round(request.amount, 2),
        status=request.status,
        reference=request.reference,
        simulated=True,
        received_at=datetime.now(timezone.utc).isoformat(),
    )
    db.add(callback)
    session.status = f"SIMULATED_{request.status}"
    db.commit()
    db.refresh(callback)
    return {
        "callback_id": callback.callback_id,
        "session_id": session_id,
        "amount": callback.amount,
        "status": callback.status,
        "reference": callback.reference,
        "simulated": True,
        "disclaimer": DISCLAIMER,
    }


@router.get("/sessions/{session_id}/ledger")
def verify_merchant_ledger(session_id: str, db: Session = Depends(get_db)):
    session = _get_session(db, session_id)
    callback = (
        db.query(SimulatedPaymentCallback)
        .filter(SimulatedPaymentCallback.session_id == session_id)
        .order_by(SimulatedPaymentCallback.received_at.desc())
        .first()
    )
    if callback is None:
        ledger_status = "UNCONFIRMED"
    elif callback.status != "SUCCESS":
        ledger_status = "SIMULATED_FAILURE"
    elif Decimal(str(callback.amount)).quantize(Decimal("0.01")) != Decimal(
        str(session.expected_amount)
    ).quantize(Decimal("0.01")):
        ledger_status = "SIMULATED_AMOUNT_MISMATCH"
    else:
        ledger_status = "SIMULATED_AMOUNT_MATCH"

    return {
        "session": _session_response(session),
        "ledger_status": ledger_status,
        "callback": (
            {
                "callback_id": callback.callback_id,
                "amount": callback.amount,
                "status": callback.status,
                "reference": callback.reference,
                "received_at": callback.received_at,
                "simulated": callback.simulated,
            }
            if callback
            else None
        ),
        "simulated": True,
        "disclaimer": DISCLAIMER,
    }
