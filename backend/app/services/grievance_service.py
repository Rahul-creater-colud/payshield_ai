"""Grievance management service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple
import uuid

from sqlalchemy.orm import Session

from app.errors import AppError, ErrorCode
from app.models import Grievance, RiskAssessment

TERMINAL = {"RESOLVED", "REJECTED"}


def create_grievance(
    db: Session,
    user_reference: str,
    assessment_id: str,
    reason: str,
    evidence_ref: Optional[str] = None,
) -> Grievance:
    if db.get(RiskAssessment, assessment_id) is None:
        raise AppError(ErrorCode.NOT_FOUND, f"Assessment {assessment_id} not found.", 404)
    now = datetime.now(timezone.utc).isoformat()
    case_id = f"CASE_{uuid.uuid4().hex[:6].upper()}"
    g = Grievance(
        case_id=case_id,
        user_reference=user_reference,
        assessment_id=assessment_id,
        reason=reason,
        evidence_ref=evidence_ref,
        status="SUBMITTED",
        reviewer_note=None,
        status_history=[{"status": "SUBMITTED", "note": None, "at": now}],
        created_at=now,
        updated_at=now,
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


def get_grievance(db: Session, case_id: str) -> Grievance:
    g = db.get(Grievance, case_id)
    if g is None:
        raise AppError(ErrorCode.NOT_FOUND, f"Grievance {case_id} not found.", 404)
    return g


def list_grievances(
    db: Session,
    status: Optional[str] = None,
    user_reference: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[Grievance], int]:
    q = db.query(Grievance)
    if status:
        q = q.filter(Grievance.status == status)
    if user_reference:
        q = q.filter(Grievance.user_reference == user_reference)
    total = q.count()
    items = q.order_by(Grievance.created_at.desc()).offset(offset).limit(limit).all()
    return items, total


def update_grievance(
    db: Session, case_id: str, new_status: str, reviewer_note: str
) -> Grievance:
    g = get_grievance(db, case_id)
    if g.status in TERMINAL:
        raise AppError(
            ErrorCode.BAD_REQUEST,
            f"Cannot update a {g.status} grievance – it is in a terminal state.",
            400,
        )
    if new_status == "SUBMITTED":
        raise AppError(ErrorCode.BAD_REQUEST, "Cannot set status back to SUBMITTED.", 400)
    now = datetime.now(timezone.utc).isoformat()
    history = list(g.status_history or [])
    history.append({"status": new_status, "note": reviewer_note, "at": now})
    g.status = new_status
    g.reviewer_note = reviewer_note
    g.status_history = history
    g.updated_at = now
    db.commit()
    db.refresh(g)
    return g
