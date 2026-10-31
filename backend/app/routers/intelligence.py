"""Fraud intelligence router."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    IntelligenceItem,
    IntelligenceListResponse,
    IntelligenceReportRequest,
    IntelligenceUpdateRequest,
)
from app.services import intelligence_service

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


def _to_item(ind, related=None) -> dict:
    return {
        "indicator_id": ind.indicator_id,
        "indicator_type": ind.indicator_type,
        "indicator_value": ind.indicator_value,
        "source": ind.source,
        "confidence": ind.confidence,
        "review_status": ind.review_status,
        "reported_at": ind.reported_at,
        "reviewed_at": ind.reviewed_at,
        "related_accounts": related or [],
    }


@router.get("")
def list_intelligence(
    type: Optional[str] = Query(default=None, alias="type"),
    review_status: Optional[str] = Query(default=None),
    min_confidence: Optional[float] = Query(default=None, ge=0, le=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = intelligence_service.list_intelligence(
        db,
        indicator_type=type,
        review_status=review_status,
        min_confidence=min_confidence,
        limit=limit,
    )
    return {
        "items": [_to_item(i) for i in items],
        "total": total,
        "data_label": "LOCAL INDICATOR RECORDS (NOT INDEPENDENTLY VERIFIED)",
    }


@router.get("/{indicator_id}")
def get_intelligence(indicator_id: str, db: Session = Depends(get_db)):
    return intelligence_service.get_intelligence(db, indicator_id)


@router.post("/report", status_code=201)
def report_intelligence(req: IntelligenceReportRequest, db: Session = Depends(get_db)):
    ind = intelligence_service.report_intelligence(
        db,
        indicator_type=req.indicator_type,
        indicator_value=req.indicator_value,
        source=req.source,
        confidence=req.confidence,
        note=req.note,
    )
    return _to_item(ind)


@router.patch("/{indicator_id}")
def update_intelligence(
    indicator_id: str, req: IntelligenceUpdateRequest, db: Session = Depends(get_db)
):
    ind = intelligence_service.update_intelligence(
        db, indicator_id=indicator_id, review_status=req.review_status, note=req.note
    )
    return _to_item(ind)
