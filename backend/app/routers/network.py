"""Account network graph router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.errors import AppError, ErrorCode
from app.schemas import NetworkResponse
from app.services.graph_service import get_account_network

router = APIRouter(prefix="/api/accounts", tags=["network"])


@router.get("/{account_id}/network", response_model=NetworkResponse)
def get_network(
    account_id: str,
    depth: int = Query(default=2, ge=1, le=3),
    db: Session = Depends(get_db),
):
    """Return the ego network around an account, with pattern detection."""
    result = get_account_network(db, account_id, depth=depth)
    if result is None:
        raise AppError(ErrorCode.NOT_FOUND, f"Account '{account_id}' not found.", 404)
    return NetworkResponse(
        center=result["center"],
        nodes=result["nodes"],
        edges=result["edges"],
        patterns=result["patterns"],
        legend=result["legend"],
    )
