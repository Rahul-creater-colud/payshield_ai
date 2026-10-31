"""Grievances router – create, retrieve, list, update."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    GrievanceCreateRequest,
    GrievanceResponse,
    GrievanceListResponse,
    GrievanceUpdateRequest,
    GrievanceAppealRequest,
    StatusHistoryEntry,
)
from app.services import grievance_service

router = APIRouter(prefix="/api/grievances", tags=["grievances"])

DISCLAIMER = "Demo grievance workflow; not an official bank grievance channel."


def _to_response(g) -> dict:
    history = [
        StatusHistoryEntry(
            status=h.get("status", ""),
            note=h.get("note"),
            at=h.get("at", ""),
        )
        for h in (g.status_history or [])
    ]
    return GrievanceResponse(
        case_id=g.case_id,
        status=g.status,
        assessment_id=g.assessment_id,
        user_reference=g.user_reference,
        reason=g.reason,
        evidence_ref=g.evidence_ref,
        reviewer_note=g.reviewer_note,
        status_history=history,
        created_at=g.created_at,
        updated_at=g.updated_at,
        disclaimer=DISCLAIMER,
    )


@router.post("", status_code=201)
def create_grievance(req: GrievanceCreateRequest, db: Session = Depends(get_db)):
    g = grievance_service.create_grievance(
        db,
        user_reference=req.user_reference,
        assessment_id=req.assessment_id,
        reason=req.reason,
        evidence_ref=req.evidence_ref,
    )
    return _to_response(g)


@router.get("/{case_id}", response_model=GrievanceResponse)
def get_grievance(case_id: str, db: Session = Depends(get_db)):
    g = grievance_service.get_grievance(db, case_id)
    return _to_response(g)


@router.get("")
def list_grievances(
    status: Optional[str] = Query(default=None),
    user_reference: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = grievance_service.list_grievances(
        db, status=status, user_reference=user_reference, limit=limit, offset=offset
    )
    return {"items": [_to_response(g).model_dump() for g in items], "total": total}


@router.patch("/{case_id}", response_model=GrievanceResponse)
def update_grievance(
    case_id: str, req: GrievanceUpdateRequest, db: Session = Depends(get_db)
):
    g = grievance_service.update_grievance(
        db, case_id=case_id, new_status=req.status, reviewer_note=req.reviewer_note
    )
    return _to_response(g)


@router.post("/{case_id}/appeals", status_code=201)
def submit_appeal(
    case_id: str,
    req: GrievanceAppealRequest,
    db: Session = Depends(get_db),
):
    appeal = grievance_service.create_appeal(db, case_id, req.reason)
    return {
        "appeal_id": appeal.appeal_id,
        "case_id": appeal.case_id,
        "reason": appeal.reason,
        "status": appeal.status,
        "created_at": appeal.created_at,
        "simulated": True,
        "disclaimer": DISCLAIMER,
    }


@router.get("/{case_id}/appeals")
def get_appeals(case_id: str, db: Session = Depends(get_db)):
    appeals = grievance_service.list_appeals(db, case_id)
    return {
        "items": [
            {
                "appeal_id": appeal.appeal_id,
                "case_id": appeal.case_id,
                "reason": appeal.reason,
                "status": appeal.status,
                "created_at": appeal.created_at,
                "simulated": True,
            }
            for appeal in appeals
        ],
        "total": len(appeals),
        "simulated": True,
        "disclaimer": DISCLAIMER,
    }
