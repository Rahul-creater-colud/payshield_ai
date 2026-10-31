"""Intelligence service – CRUD + risk scoring lookups for fraud indicators."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import uuid

from sqlalchemy.orm import Session

from app.errors import AppError, ErrorCode
from app.models import FraudIntelligence, AccountOrVPA
from app.services.audit_service import record_audit_event


def list_intelligence(
    db: Session,
    indicator_type: Optional[str] = None,
    review_status: Optional[str] = None,
    min_confidence: Optional[float] = None,
    limit: int = 20,
) -> Tuple[List[FraudIntelligence], int]:
    q = db.query(FraudIntelligence)
    if indicator_type:
        q = q.filter(FraudIntelligence.indicator_type == indicator_type)
    if review_status:
        q = q.filter(FraudIntelligence.review_status == review_status)
    if min_confidence is not None:
        q = q.filter(FraudIntelligence.confidence >= min_confidence)
    total = q.count()
    items = q.order_by(FraudIntelligence.reported_at.desc()).limit(limit).all()
    return items, total


def get_intelligence(db: Session, indicator_id: str) -> Dict[str, Any]:
    ind = db.get(FraudIntelligence, indicator_id)
    if ind is None:
        raise AppError(ErrorCode.NOT_FOUND, f"Indicator {indicator_id} not found.", 404)
    return {
        "indicator_id": ind.indicator_id,
        "indicator_type": ind.indicator_type,
        "indicator_value": ind.indicator_value,
        "source": ind.source,
        "confidence": ind.confidence,
        "review_status": ind.review_status,
        "reported_at": ind.reported_at,
        "reviewed_at": ind.reviewed_at,
        "related_accounts": _related_accounts(db, ind),
    }


def report_intelligence(
    db: Session,
    indicator_type: str,
    indicator_value: str,
    source: str,
    confidence: float,
    note: Optional[str] = None,
) -> FraudIntelligence:
    ind_id = f"IND_{uuid.uuid4().hex[:3].upper()}"
    now = datetime.now(timezone.utc).isoformat()
    ind = FraudIntelligence(
        indicator_id=ind_id,
        indicator_type=indicator_type,
        indicator_value=indicator_value,
        source=source,
        confidence=confidence,
        review_status="UNREVIEWED",
        reported_at=now,
        reviewed_at=None,
    )
    db.add(ind)
    record_audit_event(
        db,
        entity_type="intelligence_indicator",
        entity_id=ind_id,
        action="reported",
        details={"indicator_type": indicator_type, "review_status": "UNREVIEWED"},
    )
    db.commit()
    db.refresh(ind)
    return ind


def update_intelligence(
    db: Session, indicator_id: str, review_status: str, note: Optional[str] = None
) -> FraudIntelligence:
    ind = db.get(FraudIntelligence, indicator_id)
    if ind is None:
        raise AppError(ErrorCode.NOT_FOUND, f"Indicator {indicator_id} not found.", 404)
    now = datetime.now(timezone.utc).isoformat()
    ind.review_status = review_status
    ind.reviewed_at = now
    record_audit_event(
        db,
        entity_type="intelligence_indicator",
        entity_id=indicator_id,
        action="review_status_updated",
        details={"review_status": review_status},
    )
    db.commit()
    db.refresh(ind)
    return ind


def get_intel_for_risk(
    db: Session,
    receiver_id: str,
    vpa: Optional[str] = None,
    mobile: Optional[str] = None,
) -> Tuple[int, List[dict]]:
    """Return (score, reasons) for risk scoring. Ignores RETRACTED indicators."""
    acc = db.get(AccountOrVPA, receiver_id)
    values: set = set()
    if acc:
        if acc.vpa:
            values.add(acc.vpa)
        if acc.mobile:
            values.add(acc.mobile)
    if vpa:
        values.add(vpa)
    if mobile:
        values.add(mobile)

    if not values:
        return 0, []

    indicators = (
        db.query(FraudIntelligence)
        .filter(
            FraudIntelligence.indicator_value.in_(list(values)),
            FraudIntelligence.review_status != "RETRACTED",
        )
        .all()
    )

    status_mult = {"VERIFIED": 1.0, "UNREVIEWED": 0.7, "DISPUTED": 0.3}
    score = 0
    reasons: List[dict] = []
    for ind in indicators:
        mult = status_mult.get(ind.review_status, 0.5)
        weight = int(ind.confidence * mult * 40)
        score += weight
        reasons.append({
            "code": f"INTEL_{ind.indicator_type}_MATCH",
            "layer": "intelligence",
            "text": (
                f"Recipient {ind.indicator_type.lower()} ({ind.indicator_value}) "
                f"matches a fraud indicator (confidence: {ind.confidence:.0%}, "
                f"status: {ind.review_status})."
            ),
            "weight": weight,
        })

    return min(score, 100), reasons


def _related_accounts(db: Session, ind: FraudIntelligence) -> List[str]:
    if ind.indicator_type == "VPA":
        rows = db.query(AccountOrVPA).filter(AccountOrVPA.vpa == ind.indicator_value).all()
        return [r.account_id for r in rows]
    if ind.indicator_type == "MOBILE":
        rows = db.query(AccountOrVPA).filter(AccountOrVPA.mobile == ind.indicator_value).all()
        return [r.account_id for r in rows]
    return []
