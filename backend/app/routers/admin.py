"""Admin router – demo recovery (guarded by ENABLE_ADMIN setting)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, engine, Base
from app.errors import AppError, ErrorCode
from app import models  # noqa: F401 – ensure tables registered
from app.db.seed import load_seed

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/reset")
def admin_reset(db: Session = Depends(get_db)):
    """Drop all tables, recreate, and re-seed. Guarded by ENABLE_ADMIN=true."""
    if not settings.ENABLE_ADMIN:
        raise AppError(
            ErrorCode.NOT_FOUND,
            "Not found.",
            404,
        )
    db.close()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    load_seed(seed_path=settings.SEED_PATH)
    return {"status": "ok", "message": "Database reset and re-seeded successfully."}
