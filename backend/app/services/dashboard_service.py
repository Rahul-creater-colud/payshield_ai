"""Dashboard summary service."""

from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Transaction, RiskAssessment, Grievance, GraphEdge


def get_summary(db: Session) -> Dict[str, Any]:
    txn_count = db.query(func.count(Transaction.transaction_id)).scalar() or 0
    asm_count = db.query(func.count(RiskAssessment.assessment_id)).scalar() or 0
    open_grievances = (
        db.query(func.count(Grievance.case_id))
        .filter(Grievance.status.in_(["SUBMITTED", "UNDER_REVIEW", "MORE_INFO_REQUIRED"]))
        .scalar() or 0
    )

    # Risk distribution
    risk_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    for cat, cnt in (
        db.query(RiskAssessment.category, func.count(RiskAssessment.assessment_id))
        .group_by(RiskAssessment.category).all()
    ):
        if cat in risk_dist:
            risk_dist[cat] = cnt

    # Recent alerts (MEDIUM/HIGH, newest 10)
    recent_alerts = []
    for a in (
        db.query(RiskAssessment)
        .filter(RiskAssessment.category.in_(["MEDIUM", "HIGH"]))
        .order_by(RiskAssessment.created_at.desc())
        .limit(10).all()
    ):
        reasons = a.reasons or []
        top = reasons[0]["text"] if reasons else "No reason recorded"
        recent_alerts.append({
            "assessment_id": a.assessment_id,
            "transaction_id": a.transaction_id,
            "score": a.score,
            "category": a.category,
            "top_reason": top,
            "created_at": a.created_at,
        })

    # Grievance summary
    grv = {s: 0 for s in ["SUBMITTED", "UNDER_REVIEW", "MORE_INFO_REQUIRED", "RESOLVED", "REJECTED"]}
    for status, cnt in (
        db.query(Grievance.status, func.count(Grievance.case_id))
        .group_by(Grievance.status).all()
    ):
        if status in grv:
            grv[status] = cnt

    # Suspicious clusters from graph_edges fan-in
    clusters = []
    for target, src_count in (
        db.query(GraphEdge.target_account, func.count(func.distinct(GraphEdge.source_account)).label("c"))
        .group_by(GraphEdge.target_account)
        .having(func.count(func.distinct(GraphEdge.source_account)) >= settings.FAN_IN_MIN)
        .all()
    ):
        clusters.append({"center": target, "pattern": "FAN_IN", "account_count": src_count})

    return {
        "totals": {
            "transactions": txn_count,
            "assessments": asm_count,
            "open_grievances": open_grievances,
        },
        "risk_distribution": risk_dist,
        "recent_alerts": recent_alerts,
        "grievance_summary": grv,
        "suspicious_clusters": clusters,
        "data_label": "DEMO / SYNTHETIC DATA",
        "simulated": True,
    }
