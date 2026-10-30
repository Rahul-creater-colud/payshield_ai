"""Pydantic v2 request/response schemas for PayShield AI."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DISCLAIMER = (
    "Prototype using synthetic data. "
    "Risk scores are illustrative heuristics, not proof of fraud."
)

FORBIDDEN_FIELDS = {"pin", "otp", "password", "card_number", "cvv", "secret"}


# ---------------------------------------------------------------------------
# Shared / reusable
# ---------------------------------------------------------------------------
class ReasonItem(BaseModel):
    code: str
    layer: str
    text: str
    weight: int


class PlaybookMatchItem(BaseModel):
    playbook_id: str
    name: str
    warning: str
    recommended_action: str


class GraphFlagItem(BaseModel):
    pattern: str  # FAN_IN|FAN_OUT|RAPID_ONWARD|MULTI_HOP
    accounts: List[str]
    explanation: str


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    db: str
    time: str


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------
class CatalogUser(BaseModel):
    user_id: str
    display_name: str


class CatalogAccount(BaseModel):
    account_id: str
    vpa: Optional[str] = None
    label: Optional[str] = None


class ScenarioPrefill(BaseModel):
    sender_id: str
    receiver_id: str
    amount: float
    request_type: str
    context: Optional[dict] = None


class ScenarioItem(BaseModel):
    id: str
    title: str
    description: str
    prefill: ScenarioPrefill


class CatalogResponse(BaseModel):
    users: List[CatalogUser]
    accounts: List[CatalogAccount]
    request_types: List[str] = ["PAY", "COLLECT_REQUEST"]
    scenarios: List[ScenarioItem]
    grievance_statuses: List[str] = [
        "SUBMITTED", "UNDER_REVIEW", "MORE_INFO_REQUIRED", "RESOLVED", "REJECTED"
    ]
    indicator_types: List[str] = ["VPA", "MOBILE", "URL", "DOMAIN"]
    simulated: bool = True


# ---------------------------------------------------------------------------
# Risk Assessment
# ---------------------------------------------------------------------------
class RiskContext(BaseModel):
    """Optional context block sent with assessment requests."""
    message_text: Optional[str] = None
    url: Optional[str] = None
    unsolicited: bool = False
    events: Optional[List[str]] = None


class RiskAssessRequest(BaseModel):
    sender_id: str
    receiver_id: str
    amount: float = Field(..., gt=0, le=10_000_000)
    request_type: str = Field(default="PAY")
    timestamp: Optional[str] = None
    context: Optional[RiskContext] = None

    @field_validator("request_type")
    @classmethod
    def _validate_request_type(cls, v: str) -> str:
        if v not in ("PAY", "COLLECT_REQUEST"):
            raise ValueError("request_type must be PAY or COLLECT_REQUEST")
        return v

    @model_validator(mode="before")
    @classmethod
    def _reject_forbidden_fields(cls, values):
        if isinstance(values, dict):
            bad = set(values.keys()) & FORBIDDEN_FIELDS
            if bad:
                raise ValueError(
                    f"Forbidden fields detected: {', '.join(sorted(bad))}. "
                    "Never send PINs, OTPs, passwords, or card credentials."
                )
        return values


class LayerScores(BaseModel):
    behaviour: int = 0
    graph: int = 0
    playbook: int = 0
    intelligence: int = 0


class RiskAssessResponse(BaseModel):
    assessment_id: str
    transaction_id: str
    score: int = Field(..., ge=0, le=100)
    category: str  # LOW|MEDIUM|HIGH
    reasons: List[ReasonItem]
    recommended_action: str  # PROCEED|CAUTION_VERIFY|STOP_AND_REVIEW
    safety_warnings: List[str] = []
    playbook_matches: List[PlaybookMatchItem] = []
    graph_flags: List[GraphFlagItem] = []
    layer_scores: LayerScores
    collect_request_warning: Optional[str] = None
    model_version: str
    simulated: bool = True
    disclaimer: str = DISCLAIMER


# ---------------------------------------------------------------------------
# URL Scan
# ---------------------------------------------------------------------------
class URLScanRequest(BaseModel):
    url: str


class URLIndicatorItem(BaseModel):
    code: str
    text: str


class URLScanResponse(BaseModel):
    url: str
    normalized_url: str
    verdict: str  # SAFE|SUSPICIOUS|MALICIOUS|INVALID
    risk_score: int = Field(..., ge=0, le=100)
    indicators: List[URLIndicatorItem] = []
    advice: str = ""
    simulated: bool = True
    disclaimer: str = DISCLAIMER


# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------
class NetworkNode(BaseModel):
    id: str
    label: str
    risk_level: str = "LOW"
    report_status: str = "NONE"
    flags: List[str] = []


class NetworkEdge(BaseModel):
    id: int
    source: str
    target: str
    amount: float
    timestamp: str
    transaction_id: Optional[str] = None
    direction: str


class NetworkPattern(BaseModel):
    pattern: str
    accounts: List[str]
    explanation: str


class NetworkResponse(BaseModel):
    center: str
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]
    patterns: List[NetworkPattern]
    legend: dict = {}
    simulated: bool = True
    disclaimer: str = DISCLAIMER


# ---------------------------------------------------------------------------
# Grievances
# ---------------------------------------------------------------------------
class GrievanceCreateRequest(BaseModel):
    user_reference: str
    assessment_id: str
    reason: str = Field(..., min_length=10)
    evidence_ref: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _reject_forbidden(cls, values):
        if isinstance(values, dict):
            bad = set(values.keys()) & FORBIDDEN_FIELDS
            if bad:
                raise ValueError(f"Forbidden fields: {', '.join(sorted(bad))}")
        return values


class StatusHistoryEntry(BaseModel):
    status: str
    note: Optional[str] = None
    at: str


class GrievanceResponse(BaseModel):
    case_id: str
    status: str
    assessment_id: str
    user_reference: str
    reason: str
    evidence_ref: Optional[str] = None
    reviewer_note: Optional[str] = None
    status_history: List[StatusHistoryEntry] = []
    created_at: str
    updated_at: str
    disclaimer: str = "Demo grievance workflow; not an official bank grievance channel."


class GrievanceUpdateRequest(BaseModel):
    status: str
    reviewer_note: str = Field(..., min_length=1)

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: str) -> str:
        allowed = {"UNDER_REVIEW", "MORE_INFO_REQUIRED", "RESOLVED", "REJECTED"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class GrievanceListResponse(BaseModel):
    items: List[GrievanceResponse]
    total: int


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
class RiskDistribution(BaseModel):
    LOW: int = 0
    MEDIUM: int = 0
    HIGH: int = 0


class RecentAlert(BaseModel):
    assessment_id: str
    transaction_id: str
    score: int
    category: str
    top_reason: str
    created_at: str


class GrievanceSummary(BaseModel):
    SUBMITTED: int = 0
    UNDER_REVIEW: int = 0
    MORE_INFO_REQUIRED: int = 0
    RESOLVED: int = 0
    REJECTED: int = 0


class SuspiciousCluster(BaseModel):
    center: str
    pattern: str
    account_count: int


class Totals(BaseModel):
    transactions: int = 0
    assessments: int = 0
    open_grievances: int = 0


class DashboardSummaryResponse(BaseModel):
    totals: Totals
    risk_distribution: RiskDistribution
    recent_alerts: List[RecentAlert]
    grievance_summary: GrievanceSummary
    suspicious_clusters: List[SuspiciousCluster] = []
    data_label: str = "DEMO / SYNTHETIC DATA"
    simulated: bool = True


# ---------------------------------------------------------------------------
# Intelligence
# ---------------------------------------------------------------------------
class IntelligenceItem(BaseModel):
    indicator_id: str
    indicator_type: str
    indicator_value: str
    source: str
    confidence: float
    review_status: str
    reported_at: str
    reviewed_at: Optional[str] = None
    related_accounts: List[str] = []


class IntelligenceListResponse(BaseModel):
    items: List[IntelligenceItem]
    total: int
    data_label: str = "SYNTHETIC"


class IntelligenceReportRequest(BaseModel):
    indicator_type: str
    indicator_value: str
    source: str
    confidence: float = Field(..., ge=0, le=1)
    note: Optional[str] = None

    @field_validator("indicator_type")
    @classmethod
    def _validate_type(cls, v: str) -> str:
        if v not in ("VPA", "MOBILE", "URL", "DOMAIN"):
            raise ValueError("indicator_type must be VPA, MOBILE, URL, or DOMAIN")
        return v


class IntelligenceUpdateRequest(BaseModel):
    review_status: str
    note: Optional[str] = None

    @field_validator("review_status")
    @classmethod
    def _validate_status(cls, v: str) -> str:
        allowed = {"UNREVIEWED", "VERIFIED", "DISPUTED", "RETRACTED"}
        if v not in allowed:
            raise ValueError(f"review_status must be one of {allowed}")
        return v
