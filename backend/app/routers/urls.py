"""URL scanning router."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import URLScanRequest, URLScanResponse
from app.services.url_service import scan_url

router = APIRouter(prefix="/api/urls", tags=["urls"])


@router.post("/scan", response_model=URLScanResponse)
def url_scan(req: URLScanRequest, db: Session = Depends(get_db)):
    """Scan a URL for fraud indicators (no network calls, static analysis only)."""
    result = scan_url(req.url, db=db)
    return URLScanResponse(
        url=result["url"],
        normalized_url=result["normalized_url"],
        verdict=result["verdict"],
        risk_score=result["risk_score"],
        indicators=result["indicators"],
        advice=result["advice"],
    )
