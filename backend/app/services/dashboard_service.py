"""Dashboard summary service."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    Transaction,
    RiskAssessment,
    Grievance,
    GraphEdge,
    PaymentEvent,
)


_RISK_COLORS = ["#10b981", "#34d399", "#f59e0b", "#fb923c", "#ef4444"]


def _parse_timestamp(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def get_analytics(db: Session, date_range: str = "7D", txn_type: str = "ALL") -> Dict[str, Any]:
    transactions = db.query(Transaction).all()
    assessments = (
        db.query(RiskAssessment)
        .order_by(RiskAssessment.created_at.desc(), RiskAssessment.assessment_id.desc())
        .all()
    )
    latest_assessment = {}
    for assessment in assessments:
        latest_assessment.setdefault(assessment.transaction_id, assessment)

    transaction_by_id = {tx.transaction_id: tx for tx in transactions}
    classified = {
        txn_id: assessment
        for txn_id, assessment in latest_assessment.items()
        if txn_id in transaction_by_id
    }

    def category_for(tx: Transaction) -> str | None:
        assessment = classified.get(tx.transaction_id)
        return assessment.category if assessment else None

    def is_suspicious(tx: Transaction) -> bool:
        assessment = classified.get(tx.transaction_id)
        if assessment:
            return assessment.category in {"MEDIUM", "HIGH"}
        return False

    def is_stop_recommended(tx: Transaction) -> bool:
        assessment = classified.get(tx.transaction_id)
        return bool(assessment and assessment.recommended_action == "STOP_AND_REVIEW")

    now = datetime.now(timezone.utc)
    range_days = {"24H": 1, "7D": 7, "30D": 30}.get(date_range.upper(), 7)
    range_start = now - timedelta(days=range_days)

    def matches_type(tx: Transaction) -> bool:
        return txn_type.upper() == "ALL" or tx.request_type.upper() == txn_type.upper()

    filtered_transactions = [
        tx
        for tx in transactions
        if matches_type(tx)
        and (timestamp := _parse_timestamp(tx.timestamp)) is not None
        and timestamp >= range_start
    ]
    filtered_assessed_transactions = [
        tx for tx in filtered_transactions if tx.transaction_id in classified
    ]
    filtered_assessments = [
        classified[tx.transaction_id] for tx in filtered_assessed_transactions
    ]

    assessed_count = len(classified)
    safe_count = sum(category_for(tx) == "LOW" for tx in transactions)
    suspicious_count = sum(is_suspicious(tx) for tx in transactions)
    stop_recommendations = sum(is_stop_recommended(tx) for tx in transactions)
    provider_block_events = (
        db.query(func.count(PaymentEvent.event_id))
        .filter(
            PaymentEvent.status == "BLOCKED",
            PaymentEvent.simulated.is_(False),
            PaymentEvent.verified_at.is_not(None),
            PaymentEvent.provider_reference.is_not(None),
        )
        .scalar()
        or 0
    )

    daily = defaultdict(lambda: {
        "totalVolume": 0,
        "safeVolume": 0,
        "suspiciousVolume": 0,
        "stopReviewVolume": 0,
    })
    hourly = defaultdict(int)
    for tx in filtered_assessed_transactions:
        timestamp = _parse_timestamp(tx.timestamp)
        if timestamp is None:
            continue
        day = timestamp.date().isoformat()
        daily[day]["totalVolume"] += 1
        daily[day]["safeVolume"] += int(category_for(tx) == "LOW")
        daily[day]["suspiciousVolume"] += int(is_suspicious(tx))
        daily[day]["stopReviewVolume"] += int(is_stop_recommended(tx))
        hourly[timestamp.strftime("%H:00")] += 1

    daily_activity = [
        {
            "day": datetime.fromisoformat(day).strftime("%a"),
            "date": day,
            **counts,
        }
        for day, counts in sorted(daily.items())
    ]

    score_ranges = [
        ("0 - 20", 0, 20),
        ("21 - 40", 21, 40),
        ("41 - 60", 41, 60),
        ("61 - 80", 61, 80),
        ("81 - 100", 81, 100),
    ]
    risk_distribution = []
    for index, (label, lower, upper) in enumerate(score_ranges):
        count = sum(lower <= assessment.score <= upper for assessment in filtered_assessments)
        risk_distribution.append({
            "range": label,
            "count": count,
            "color": _RISK_COLORS[index],
            "percent": round(count * 100 / len(filtered_assessments), 1)
            if filtered_assessments else 0,
        })

    types = sorted({tx.request_type for tx in filtered_transactions})
    transaction_types = []
    for payment_type in types:
        items = [tx for tx in filtered_transactions if tx.request_type == payment_type]
        assessed_items = [tx for tx in items if tx.transaction_id in classified]
        transaction_types.append({
            "type": payment_type,
            "safe": sum(category_for(tx) == "LOW" for tx in assessed_items),
            "suspicious": sum(is_suspicious(tx) for tx in assessed_items),
            "stopReview": sum(is_stop_recommended(tx) for tx in assessed_items),
            "assessed": len(assessed_items),
            "total": len(assessed_items),
        })

    return {
        "success": True,
        "metrics": {
            "totalTransactions": len(transactions),
            "safeTransactions": safe_count,
            "suspiciousTransactions": suspicious_count,
            "blockedTransactions": provider_block_events,
            "stopReviewRecommendations": stop_recommendations,
            "assessedTransactions": assessed_count,
            "totalFraudPreventedAmount": None,
            "fraudRatePercent": None,
            "safeRatePercent": None,
            "suspiciousAssessmentRatePercent": round(suspicious_count * 100 / assessed_count, 1)
            if assessed_count else None,
            "lowRiskAssessmentRatePercent": round(safe_count * 100 / assessed_count, 1)
            if assessed_count else None,
        },
        "dailyActivity": daily_activity,
        "riskDistribution": risk_distribution,
        "transactionTypes": transaction_types,
        "transactionTypesVolume": transaction_types,
        "hourlyTraffic": [
            {"hour": hour, "volume": count}
            for hour, count in sorted(hourly.items())
        ],
        "data_label": "DEMO / SYNTHETIC DATA",
        "simulated": True,
        "detection_engine": "rule-based heuristics",
        "payment_provider_integration": False,
        "updated_at": now.isoformat(),
        "date_range": date_range.upper(),
        "transaction_type_filter": txn_type.upper(),
    }


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
