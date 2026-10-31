"""Health check endpoint."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.services.ml_model_service import ml_model_service

router = APIRouter()


def _health_check(db: Session) -> dict:
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "service": "payshield-backend",
        "version": settings.MODEL_VERSION,
        "db": db_status,
        "detection_engine": "rule-based heuristics",
        "ml_model": ml_model_service.status(),
        "payment_provider_integration": False,
        "simulated": True,
        "data_label": "DEMO / SYNTHETIC DATA",
        "time": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health")
def health_root(db: Session = Depends(get_db)):
    return _health_check(db)


@router.get("/api/health")
def health_api(db: Session = Depends(get_db)):
    return _health_check(db)
