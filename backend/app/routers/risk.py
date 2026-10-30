"""Risk assessment router."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import RiskAssessRequest, RiskAssessResponse
from app.services import risk_service

router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.post("/assess", response_model=RiskAssessResponse, status_code=200)
def assess(req: RiskAssessRequest, db: Session = Depends(get_db)):
    """Run a full risk assessment for a payment or collect request."""
    result = risk_service.assess(db, req)
    return result


@router.get("/assessments/{assessment_id}", response_model=RiskAssessResponse)
def get_assessment(assessment_id: str, db: Session = Depends(get_db)):
    """Retrieve a stored risk assessment by ID."""
    return risk_service.get_assessment(db, assessment_id)


@router.get("/assessments")
def list_assessments(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List recent risk assessments."""
    return risk_service.list_assessments(db, limit=limit)
