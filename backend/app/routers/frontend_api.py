"""Frontend Integration Router for UPI Fraud Shield (FastAPI /api/v1/...).

Connects the React frontend to the local PayShield rule-based engine:
  - GET  /api/v1/health
  - POST /api/v1/fraud/analyze
  - GET  /api/v1/transactions
  - GET  /api/v1/transactions/{id}
  - GET  /api/v1/collect-requests
  - POST /api/v1/collect-requests/{id}/action
  - GET  /api/v1/fraud/analytics
  - POST /api/v1/fraud/screenshot-ocr
  - GET  /api/v1/fraud/alerts
  - POST /api/v1/fraud/alerts/{id}/resolve
"""

from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, File, UploadFile, Form
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.config import settings
from app.database import get_db
from app import models
from app.errors import AppError, ErrorCode
from app.engine import behaviour as behaviour_engine
from app.engine import graph_layer as graph_engine
from app.engine import playbooks as playbook_engine
from app.engine import scoring as scoring_engine
from app.services import (
    url_service,
    graph_service,
    intelligence_service,
    llm_service,
)
from app.services.ml_model_service import (
    build_transaction_features,
    ml_model_service,
)
from app.services.dashboard_service import get_analytics

router = APIRouter(prefix="/api/v1", tags=["frontend_v1"])


# ---------------------------------------------------------------------------
# Request & Response Schemas
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    transaction_id: Optional[str] = None
    sender_upi: str
    receiver_upi: str
    amount: float
    transaction_time: Optional[str] = None
    transaction_type: str = "P2P"


class CollectActionRequest(BaseModel):
    action: str = Field(..., description="ACCEPT or REJECT")


class AlertResolveRequest(BaseModel):
    notes: Optional[str] = ""


# Deprecated synthetic examples; live collect-request routes never return these.
DEFAULT_COLLECT_REQUESTS = [
    {
        "id": "col-201",
        "senderName": "Customer Support Refund Desk",
        "senderUpi": "refund-support-desk88@ybl",
        "amount": 19500.00,
        "requestedAt": "2026-10-30T17:15:00+05:30",
        "expiresAt": "2026-10-30T18:15:00+05:30",
        "status": "PENDING",
        "riskScore": 96,
        "riskCategory": "HIGH",
        "warningType": "REFUND_IMPERSONATION",
        "warningTitle": "Critical Alert: Reverse Debit Phishing Attempt",
        "warningMessage": "The requester is pretending to issue a refund or lottery reward, but this is a COLLECT REQUEST that will DEBIT ₹19,500 from your bank account immediately.",
        "fraudTriggers": [
            "Fraudulent narrative: Claiming to send a refund via collect request (UPI does not require PIN to receive money)",
            "Sender VPA was registered less than 72 hours ago",
            "Multiple user complaints for fake refund scams associated with this bank node",
            "Urgency trigger: 'Immediate action required within 60 mins'",
        ],
        "verifiedMerchant": False,
        "recommendedAction": "STOP_REVIEW_RECOMMENDED",
    },
    {
        "id": "col-202",
        "senderName": "OLX Verification Center",
        "senderUpi": "olx-escrow-payment@okaxis",
        "amount": 8900.00,
        "requestedAt": "2026-10-30T16:45:20+05:30",
        "expiresAt": "2026-10-30T17:45:20+05:30",
        "status": "PENDING",
        "riskScore": 88,
        "riskCategory": "HIGH",
        "warningType": "MARKETPLACE_ADVANCE_DEBIT",
        "warningTitle": "High Danger: Fake Buyer Escrow Collect Request",
        "warningMessage": "A buyer claiming to buy your listed item has sent a request asking for ₹8,900 under the pretext of 'escrow advance verification'. You will lose ₹8,900 if you accept.",
        "fraudTriggers": [
            "OLX/Quikr buyer reverse scam detected",
            "Non-merchant personal UPI ID disguised with 'escrow' keyword",
            "Payer does not have prior payment history with recipient",
        ],
        "verifiedMerchant": False,
        "recommendedAction": "STOP_REVIEW_RECOMMENDED",
    },
    {
        "id": "col-203",
        "senderName": "Dr. Alok Verma Clinic",
        "senderUpi": "dr.alokverma@hdfcbank",
        "amount": 1200.00,
        "requestedAt": "2026-10-30T15:20:10+05:30",
        "expiresAt": "2026-10-30T18:20:10+05:30",
        "status": "PENDING",
        "riskScore": 48,
        "riskCategory": "MEDIUM",
        "warningType": "FIRST_TIME_INDIVIDUAL_COLLECT",
        "warningTitle": "Caution: First-Time Collect Request",
        "warningMessage": "This collect request is from a first-time individual payee. Verify that you scheduled this consultation before entering your UPI PIN.",
        "fraudTriggers": [
            "New individual payee requesting payment",
            "No historical transactions between sender and receiver",
            "Standard clinic consult fee request",
        ],
        "verifiedMerchant": False,
        "recommendedAction": "VERIFY_IDENTITY",
    },
    {
        "id": "col-204",
        "senderName": "Zomato Online Ordering",
        "senderUpi": "zomato.order@icici",
        "amount": 640.00,
        "requestedAt": "2026-10-30T14:10:00+05:30",
        "expiresAt": "2026-10-30T14:40:00+05:30",
        "status": "PENDING",
        "riskScore": 8,
        "riskCategory": "LOW",
        "warningType": "DEMO_SAMPLE",
        "warningTitle": "Low-Risk Demo Collect Request",
        "warningMessage": "Synthetic example only. PayShield did not verify this merchant or collect request.",
        "fraudTriggers": [
            "No external merchant or payment-provider checks were performed",
        ],
        "verifiedMerchant": False,
        "recommendedAction": "REVIEW_ONLY",
    },
]

# Synthetic alert examples served only by the deprecated /demo route.
DEFAULT_ALERTS = [
    {
        "id": "alt-501",
        "severity": "CRITICAL",
        "category": "HIGH",
        "riskScore": 98,
        "title": "Nocturnal High-Value Outflow to High-Risk Mule Account",
        "detectedAt": "2026-10-30T02:35:10+05:30",
        "affectedAccount": "ananya.sen@ybl",
        "suspectEntity": "fastpay.crypto99@airtel",
        "amount": 45000.00,
        "status": "INVESTIGATING",
        "ruleBroken": "R-702: Nocturnal Unusual Spike + Money Mule Pattern",
        "explanation": "A ₹45,000 transaction was initiated at 2:35 AM to a newly provisioned virtual payment address flagged for receiving rapid sequential deposits and immediate crypto off-ramping. The payer's habitual profile shows zero transactions between 11 PM and 6 AM.",
        "indicators": [
            "Device IMEI is unrecognised",
            "Velocity: 3 attempts within 15 minutes",
            "Beneficiary UPI handle registered under suspect Airtel Payments Bank node",
        ],
        "recommendedActions": [
            "Review this synthetic assessment; no account controls are available",
            "Contact the account holder using an independently verified channel",
            "Refer to an authorized fraud response channel outside this demo",
        ],
    },
    {
        "id": "alt-502",
        "severity": "CRITICAL",
        "category": "HIGH",
        "riskScore": 94,
        "title": "Bank Impersonation KYC Phishing Collect Request",
        "detectedAt": "2026-10-30T16:15:30+05:30",
        "affectedAccount": "pooja.patel@icici",
        "suspectEntity": "sbi-kyc-update-desk@ybl",
        "amount": 24999.00,
        "status": "STOP_RECOMMENDED",
        "ruleBroken": "R-305: Financial Entity Name Impersonation & Reverse Debit",
        "explanation": "A collect request asking for ₹24,999 was sent to the user using the handle 'sbi-kyc-update-desk@ybl'. Scammers often send SMS warnings threatening account freeze unless KYC is verified, followed by a collect request falsely claimed to be a verification deposit.",
        "indicators": [
            "VPA handle contains restricted bank trademark keyword 'sbi'",
            "Sender VPA was registered via third-party PSP",
            "Reverse debit trick targeting non-technical users",
        ],
        "recommendedActions": [
            "Review this synthetic assessment; no account controls are available",
            "Verify any real incident independently with the relevant organization",
            "Do not interpret this synthetic example as a confirmed fraud report",
        ],
    },
    {
        "id": "alt-503",
        "severity": "HIGH",
        "category": "HIGH",
        "riskScore": 92,
        "title": "Typosquatting Government Relief Fund Spoof",
        "detectedAt": "2026-10-29T10:05:14+05:30",
        "affectedAccount": "kunal.b@oksbi",
        "suspectEntity": "pm-relief-fund-2026@ibl",
        "amount": 5000.00,
        "status": "STOP_RECOMMENDED",
        "ruleBroken": "R-411: Brand/NGO Trademark Infringement in UPI Handle",
        "explanation": "Target recipient handle mimicked the Prime Minister's Relief Fund with a deceptive handle '@ibl' instead of '@sbi'.",
        "indicators": [
            "Levenshtein distance <= 2 from official PM-CARES handle",
            "Domain not whitelisted under official gov.in payment entities",
        ],
        "recommendedActions": [
            "Review this synthetic assessment; PayShield cannot intercept payments",
            "Use authorized reporting channels only if a real incident is independently confirmed",
        ],
    },
    {
        "id": "alt-504",
        "severity": "MEDIUM",
        "category": "MEDIUM",
        "riskScore": 68,
        "title": "Infant QR Merchant Rapid Surge Anomaly",
        "detectedAt": "2026-10-29T19:42:00+05:30",
        "affectedAccount": "rohan.d@oksbi",
        "suspectEntity": "metro.gadgets@razorpay",
        "amount": 18400.00,
        "status": "INVESTIGATING",
        "ruleBroken": "R-504: Merchant Inception Under 48h with High Outflow",
        "explanation": "A newly registered merchant QR code received 42 high-value payments within 6 hours of account activation.",
        "indicators": [
            "Merchant age < 48 hours",
            "Average transaction size 8x higher than peer retail category",
        ],
        "recommendedActions": [
            "Apply 24-hour settlement hold on merchant wallet",
            "Request merchant GSTIN and physical store verification photos",
        ],
    },
]


# ---------------------------------------------------------------------------
# 1. Health & Connectivity Check
# ---------------------------------------------------------------------------
@router.get("/health")
def api_v1_health(db: Session = Depends(get_db)):
    """Reports local service and database availability without implying external access."""
    db.execute(models.Transaction.__table__.select().limit(1))
    return {
        "status": "healthy",
        "version": settings.MODEL_VERSION,
        "db": "ok",
        "detection_engine": "rule-based heuristics",
        "ml_model": ml_model_service.status(),
        "payment_provider_integration": False,
        "data_label": "DEMO / SYNTHETIC DATA",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "simulated": True,
    }


# ---------------------------------------------------------------------------
# 2. Real-Time Transaction Risk Analysis
# ---------------------------------------------------------------------------
@router.post("/fraud/analyze")
def api_v1_analyze_transaction(req: AnalyzeRequest, db: Session = Depends(get_db)):
    """Assess and store a submitted record; no payment is executed or blocked."""
    txn_id = req.transaction_id or f"UPI/{datetime.now(timezone.utc).year}/{uuid.uuid4().hex[:9]}"
    ts_str = req.transaction_time or datetime.now(timezone.utc).isoformat()

    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AppError(
            ErrorCode.BAD_REQUEST,
            "transaction_time must be a valid ISO 8601 timestamp",
            status_code=422,
        ) from exc
    hour = ts.hour

    sender_upi_clean = req.sender_upi.strip().lower()
    receiver_upi_clean = req.receiver_upi.strip().lower()
    sender_history = (
        db.query(models.Transaction)
        .filter(func.lower(func.trim(models.Transaction.sender_id)) == sender_upi_clean)
        .all()
    )
    model_features, model_assumptions = build_transaction_features(
        req.amount,
        ts,
        sender_history,
        req.receiver_upi,
        exclude_transaction_id=txn_id,
    )
    ml_assessment = ml_model_service.predict(
        model_features, model_assumptions
    )

    # Pre-parse name from VPA
    def _vpa_to_name(vpa: str) -> str:
        part = vpa.split("@")[0].replace(".", " ").replace("-", " ").replace("_", " ")
        return part.title()

    sender_name = _vpa_to_name(req.sender_upi)
    receiver_name = _vpa_to_name(req.receiver_upi)

    # 1. Heuristic Indicators
    is_night = (hour < 6 or hour >= 23)
    is_collect = (req.transaction_type == "COLLECT_REQUEST")
    is_phish_vpa = any(
        kw in receiver_upi_clean
        for kw in ["kyc", "refund", "support", "desk", "reward", "lottery", "winner", "update", "verify"]
    )
    is_mule_vpa = any(
        kw in receiver_upi_clean
        for kw in ["crypto", "mule", "fastpay", "acc_300", "airtel"]
    )
    is_brand_spoof = any(
        kw in receiver_upi_clean
        for kw in ["sbi", "hdfc", "icici", "phonepe", "paytm", "gpay", "bhim"]
    ) and not any(
        legit in receiver_upi_clean
        for legit in ["@icici", "@okhdfcbank", "@okaxis", "@oksbi"]
    )

    # Intelligence query
    intel_hit = (
        db.query(models.FraudIntelligence)
        .filter(
            models.FraudIntelligence.indicator_value.ilike(f"%{receiver_upi_clean}%"),
            models.FraudIntelligence.review_status != "RETRACTED",
        )
        .first()
    )

    reasons: List[str] = []
    score = 10

    if is_phish_vpa:
        score = max(score, 92)
        reasons.append("Impersonation tactic: UPI handle mimics official verification/refund department")
    if is_collect:
        score = max(score, 65)
        reasons.append("Reverse debit vector: payment request incoming under pretense of credit/refund")
    if is_mule_vpa or (is_night and req.amount > 20000):
        score = max(score, 95)
        reasons.append("Nocturnal high-value velocity anomaly with mule beneficiary heuristics")
    if intel_hit:
        score = max(score, 94)
        reasons.append(f"VPA handle reported in Threat Intelligence Registry ({intel_hit.source})")
    if is_brand_spoof:
        score = max(score, 88)
        reasons.append("Typosquatting/brand spoof: Private handle using commercial bank name")
    if req.amount > 20000 and score < 40:
        score = 45
        reasons.append("High transaction value above baseline standard deviation")
    if not reasons:
        reasons.append("Frequent contact with verified transaction history")
        reasons.append("Amount within normal standard deviation for sender")
        score = min(score, 18)

    # Categorise
    if score >= 70:
        category = "HIGH"
        status = "STOP_RECOMMENDED"
    elif score >= 40:
        category = "MEDIUM"
        status = "FLAGGED"
    else:
        category = "LOW"
        status = "SAFE"

    # Specific indicators
    indicators = {
        "newDevice": is_night or score >= 70,
        "unusualTime": is_night,
        "velocityAlert": is_mule_vpa or (req.amount > 30000),
        "blacklistedReceiver": bool(intel_hit or is_phish_vpa),
        "mismatchedVPA": is_brand_spoof or is_phish_vpa,
        "collectRequestAnomaly": is_collect,
    }

    # Persist record into transactions & risk_assessments for audit trail
    try:
        db_txn = models.Transaction(
            transaction_id=txn_id,
            sender_id=req.sender_upi,
            receiver_id=req.receiver_upi,
            amount=req.amount,
            timestamp=ts_str,
            status=status,
            request_type=req.transaction_type,
        )
        db.merge(db_txn)

        asm_id = f"ASM_{uuid.uuid4().hex[:8].upper()}"
        db_asm = models.RiskAssessment(
            assessment_id=asm_id,
            transaction_id=txn_id,
            score=score,
            category=category,
            reasons=[{"code": "ANALYSIS_FLAG", "layer": "rule_engine", "text": r, "weight": 20} for r in reasons],
            recommended_action="STOP_AND_REVIEW" if category == "HIGH" else ("CAUTION_VERIFY" if category == "MEDIUM" else "PROCEED"),
            playbook_matches=[],
            model_version=settings.MODEL_VERSION,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        db.merge(db_asm)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise AppError(
            ErrorCode.INTERNAL_ERROR,
            "Transaction assessment could not be recorded",
            status_code=500,
        ) from exc

    return {
        "success": True,
        "data": {
            "transactionId": txn_id,
            "senderName": sender_name,
            "senderUpi": req.sender_upi,
            "receiverName": receiver_name,
            "receiverUpi": req.receiver_upi,
            "amount": req.amount,
            "timestamp": ts_str,
            "type": req.transaction_type,
            "status": status,
            "riskScore": score,
            "riskCategory": category,
            "recommendedAction": "STOP_AND_REVIEW" if category == "HIGH" else (
                "CAUTION_VERIFY" if category == "MEDIUM" else "PROCEED"
            ),
            "reasons": reasons,
            "indicators": indicators,
            "ml_model": ml_assessment,
            "simulated": True,
            "data_label": "DEMO / SYNTHETIC DATA",
            "payment_executed": False,
        },
    }


# ---------------------------------------------------------------------------
# 3. Transaction History Log
# ---------------------------------------------------------------------------
@router.get("/demo/transactions", deprecated=True)
def api_v1_get_transactions(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query("ALL"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Retrieve logged transactions with risk assessment details."""
    query = db.query(models.Transaction).order_by(desc(models.Transaction.timestamp))
    if status and status != "ALL":
        query = query.filter(models.Transaction.status == status)

    db_txns = query.limit(limit).all()
    results = []

    for tx in db_txns:
        if search:
            s = search.lower()
            if (
                s not in tx.transaction_id.lower()
                and s not in tx.sender_id.lower()
                and s not in tx.receiver_id.lower()
            ):
                continue

        # Look up assessment
        asm = db.query(models.RiskAssessment).filter_by(transaction_id=tx.transaction_id).first()
        score = asm.score if asm else (90 if tx.status == "BLOCKED" else (50 if tx.status == "FLAGGED" else 15))
        category = asm.category if asm else ("HIGH" if score >= 70 else ("MEDIUM" if score >= 40 else "LOW"))
        reasons_raw = [r["text"] for r in (asm.reasons or []) if isinstance(r, dict) and "text" in r] if asm else [
            "Transaction assessed by rules engine."
        ]

        def _name(val: str) -> str:
            return val.split("@")[0].replace(".", " ").replace("-", " ").title()

        results.append({
            "id": f"tx-{tx.transaction_id}",
            "transactionId": tx.transaction_id,
            "senderName": _name(tx.sender_id),
            "senderUpi": tx.sender_id,
            "receiverName": _name(tx.receiver_id),
            "receiverUpi": tx.receiver_id,
            "amount": tx.amount,
            "timestamp": tx.timestamp,
            "type": tx.request_type,
            "status": (
                "STOP_RECOMMENDED" if tx.status == "BLOCKED" or category == "HIGH"
                else "FLAGGED" if tx.status in {"FLAGGED", "SUSPICIOUS"}
                else "SAFE" if tx.status == "SAFE"
                else "UNASSESSED"
            ),
            "riskScore": score,
            "riskCategory": category,
            "reasons": reasons_raw or ["Automated behavioral check"],
        })

    # If DB has very few transactions, append sample entries to keep frontend view rich
    if len(results) < 5:
        from app.routers import catalog
        # Supplement with standard demo records
        seed_samples = [
            {
                "id": "tx-101",
                "transactionId": "UPI/2026/894729104",
                "senderName": "Aarav Sharma",
                "senderUpi": "aarav.sharma@okaxis",
                "receiverName": "Kavita Verma",
                "receiverUpi": "kavita.v@okhdfcbank",
                "amount": 1450.00,
                "timestamp": "2026-10-30T17:42:15+05:30",
                "type": "P2P",
                "status": "SAFE",
                "riskScore": 12,
                "riskCategory": "LOW",
                "reasons": ["Frequent contact with verified transaction history"],
            },
            {
                "id": "tx-102",
                "transactionId": "UPI/2026/993821034",
                "senderName": "Pooja Patel",
                "senderUpi": "pooja.patel@icici",
                "receiverName": "KYC Verification Support",
                "receiverUpi": "sbi-kyc-update-desk@ybl",
                "amount": 24999.00,
                "timestamp": "2026-10-30T16:15:30+05:30",
                "type": "COLLECT_REQUEST",
                "status": "STOP_RECOMMENDED",
                "riskScore": 94,
                "riskCategory": "HIGH",
                "reasons": ["Impersonation tactic: UPI handle mimics official bank KYC department"],
            },
            {
                "id": "tx-103",
                "transactionId": "UPI/2026/772819022",
                "senderName": "Ananya Sen",
                "senderUpi": "ananya.sen@ybl",
                "receiverName": "Fastpay Crypto Services",
                "receiverUpi": "fastpay.crypto99@airtel",
                "amount": 45000.00,
                "timestamp": "2026-10-30T02:35:10+05:30",
                "type": "P2P",
                "status": "STOP_RECOMMENDED",
                "riskScore": 98,
                "riskCategory": "HIGH",
                "reasons": ["Nocturnal Unusual Spike + Money Mule Pattern"],
            },
        ]
        results.extend(seed_samples)

    return {
        "success": True,
        "total": len(results),
        "data": results,
        "data_label": "DEMO DATA — legacy sample route",
        "simulated": True,
    }


@router.get("/demo/transactions/{txn_id}", deprecated=True)
def api_v1_get_transaction_detail(txn_id: str, db: Session = Depends(get_db)):
    """Retrieve single transaction detail."""
    clean_id = txn_id.replace("tx-", "")
    tx = db.query(models.Transaction).filter_by(transaction_id=clean_id).first()
    if not tx:
        # Fallback sample
        return {
            "success": True,
            "data_label": "DEMO DATA — legacy sample route",
            "simulated": True,
            "data": {
                "id": txn_id,
                "transactionId": clean_id,
                "senderName": "Aarav Sharma",
                "senderUpi": "aarav.sharma@okaxis",
                "receiverName": "Kavita Verma",
                "receiverUpi": "kavita.v@okhdfcbank",
                "amount": 1450.00,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "P2P",
                "status": "SAFE",
                "riskScore": 12,
                "riskCategory": "LOW",
                "reasons": ["Frequent contact with verified transaction history"],
                "indicators": {"newDevice": False, "unusualTime": False, "velocityAlert": False},
            },
        }

    asm = db.query(models.RiskAssessment).filter_by(transaction_id=tx.transaction_id).first()
    score = asm.score if asm else 20
    category = asm.category if asm else "LOW"
    reasons = [r["text"] for r in (asm.reasons or []) if isinstance(r, dict)] if asm else []

    return {
        "success": True,
        "data_label": "DEMO DATA — legacy sample route",
        "simulated": True,
        "data": {
            "id": f"tx-{tx.transaction_id}",
            "transactionId": tx.transaction_id,
            "senderName": tx.sender_id.split("@")[0].title(),
            "senderUpi": tx.sender_id,
            "receiverName": tx.receiver_id.split("@")[0].title(),
            "receiverUpi": tx.receiver_id,
            "amount": tx.amount,
            "timestamp": tx.timestamp,
            "type": tx.request_type,
            "status": "STOP_RECOMMENDED" if tx.status == "BLOCKED" else tx.status,
            "riskScore": score,
            "riskCategory": category,
            "reasons": reasons,
            "indicators": {"newDevice": False, "unusualTime": False, "velocityAlert": False},
        },
    }


def _transaction_response(tx: models.Transaction, assessment: Optional[models.RiskAssessment]) -> Dict[str, Any]:
    def _name(value: str) -> str:
        return value.split("@")[0].replace(".", " ").replace("-", " ").replace("_", " ").title()

    category = assessment.category if assessment else "UNASSESSED"
    if category == "HIGH":
        status = "STOP_RECOMMENDED"
    elif category == "MEDIUM":
        status = "FLAGGED"
    elif category == "LOW":
        status = "SAFE"
    elif tx.status in {"SAFE", "FLAGGED", "SUSPICIOUS"}:
        status = "FLAGGED" if tx.status == "SUSPICIOUS" else tx.status
    else:
        status = "UNASSESSED"

    reasons = [
        reason["text"]
        for reason in (assessment.reasons or [])
        if isinstance(reason, dict) and reason.get("text")
    ] if assessment else []

    return {
        "id": f"tx-{tx.transaction_id}",
        "transactionId": tx.transaction_id,
        "senderName": _name(tx.sender_id),
        "senderUpi": tx.sender_id,
        "receiverName": _name(tx.receiver_id),
        "receiverUpi": tx.receiver_id,
        "amount": tx.amount,
        "timestamp": tx.timestamp,
        "type": tx.request_type,
        "status": status,
        "riskScore": assessment.score if assessment else None,
        "riskCategory": category,
        "recommendedAction": assessment.recommended_action if assessment else None,
        "assessmentId": assessment.assessment_id if assessment else None,
        "reasons": reasons,
        "simulated": True,
        "data_label": "DEMO / SYNTHETIC DATA",
    }


@router.get("/transactions")
def api_v1_get_stored_transactions(
    search: Optional[str] = Query(None),
    status: str = Query("ALL"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Return stored transactions and their latest persisted risk assessment."""
    transactions = (
        db.query(models.Transaction)
        .order_by(desc(models.Transaction.timestamp))
        .all()
    )
    assessments = (
        db.query(models.RiskAssessment)
        .order_by(desc(models.RiskAssessment.created_at), desc(models.RiskAssessment.assessment_id))
        .all()
    )
    latest = {}
    for assessment in assessments:
        latest.setdefault(assessment.transaction_id, assessment)

    requested_status = status.upper()
    if requested_status == "SUSPICIOUS":
        requested_status = "FLAGGED"
    query = (search or "").strip().lower()
    results = []
    for tx in transactions:
        item = _transaction_response(tx, latest.get(tx.transaction_id))
        if requested_status != "ALL" and item["status"] != requested_status:
            continue
        if query and not any(
            query in str(item[field]).lower()
            for field in ("transactionId", "senderName", "senderUpi", "receiverName", "receiverUpi")
        ):
            continue
        results.append(item)

    return {
        "success": True,
        "total": len(results),
        "data": results[:limit],
        "data_label": "DEMO / SYNTHETIC DATA",
        "simulated": True,
    }


@router.get("/transactions/{txn_id}")
def api_v1_get_stored_transaction_detail(txn_id: str, db: Session = Depends(get_db)):
    clean_id = txn_id.removeprefix("tx-")
    tx = db.get(models.Transaction, clean_id)
    if tx is None:
        raise AppError(ErrorCode.NOT_FOUND, "Stored transaction not found", status_code=404)
    assessment = (
        db.query(models.RiskAssessment)
        .filter_by(transaction_id=clean_id)
        .order_by(desc(models.RiskAssessment.created_at), desc(models.RiskAssessment.assessment_id))
        .first()
    )
    return {
        "success": True,
        "data": _transaction_response(tx, assessment),
    }


# ---------------------------------------------------------------------------
# 4. Collect Request Interception Shield
# ---------------------------------------------------------------------------
@router.get("/collect-requests")
def api_v1_get_collect_requests():
    """No live UPI collect-request feed is configured for this local prototype."""
    return {
        "success": True,
        "total": 0,
        "data": [],
        "available": False,
        "data_label": "UNAVAILABLE — no authorized payment-provider integration",
    }


@router.post("/collect-requests/{req_id}/action")
def api_v1_action_collect_request(req_id: str, body: CollectActionRequest):
    """Reject actions because the prototype cannot receive or control live requests."""
    raise AppError(
        ErrorCode.BAD_REQUEST,
        "Live collect-request actions are unavailable without an authorized payment-provider integration",
        status_code=501,
    )


# ---------------------------------------------------------------------------
# 5. Fraud Analytics
# ---------------------------------------------------------------------------
@router.get("/demo/fraud/analytics", deprecated=True)
def api_v1_get_fraud_analytics(
    dateRange: Optional[str] = Query("7D"),
    txnType: Optional[str] = Query("ALL"),
    db: Session = Depends(get_db),
):
    """Return deprecated synthetic analytics for explicit demo use only."""
    total_txns = db.query(models.Transaction).count()
    total_assessments = db.query(models.RiskAssessment).count()

    return {
        "success": True,
        "data_label": "DEMO DATA — legacy static analytics, not live records",
        "simulated": True,
        "detection_engine": "rule-based heuristics",
        "payment_provider_integration": False,
        "metrics": {
            "totalTransactions": max(148920, total_txns + 148900),
            "safeTransactions": max(142380, total_txns + 142000),
            "suspiciousTransactions": 4890 + total_assessments,
            "blockedTransactions": 0,
            "stopReviewRecommendations": 1650,
            "totalFraudPreventedAmount": None,
            "fraudRatePercent": 1.11,
            "safeRatePercent": 95.61,
        },
        "dailyActivity": [
            {"day": "Mon", "date": "2026-10-24", "totalVolume": 18400, "safeVolume": 17620, "suspiciousVolume": 560, "stopReviewVolume": 220},
            {"day": "Tue", "date": "2026-10-25", "totalVolume": 21200, "safeVolume": 20280, "suspiciousVolume": 690, "stopReviewVolume": 230},
            {"day": "Wed", "date": "2026-10-26", "totalVolume": 19800, "safeVolume": 18940, "suspiciousVolume": 610, "stopReviewVolume": 250},
            {"day": "Thu", "date": "2026-10-27", "totalVolume": 23400, "safeVolume": 22350, "suspiciousVolume": 790, "stopReviewVolume": 260},
            {"day": "Fri", "date": "2026-10-28", "totalVolume": 24900, "safeVolume": 23780, "suspiciousVolume": 820, "stopReviewVolume": 300},
            {"day": "Sat", "date": "2026-10-29", "totalVolume": 28500, "safeVolume": 27150, "suspiciousVolume": 980, "stopReviewVolume": 370},
            {"day": "Sun", "date": "2026-10-30", "totalVolume": 22720, "safeVolume": 21760, "suspiciousVolume": 740, "stopReviewVolume": 220},
        ],
        "riskDistribution": [
            {"range": "0 - 20 (Safe)", "count": 128400, "color": "#10b981", "percent": 86.2},
            {"range": "21 - 40 (Low Risk)", "count": 13980, "color": "#34d399", "percent": 9.4},
            {"range": "41 - 60 (Medium Risk)", "count": 3250, "color": "#f59e0b", "percent": 2.2},
            {"range": "61 - 80 (High Suspicion)", "count": 1640, "color": "#fb923c", "percent": 1.1},
            {"range": "81 - 100 (High Risk)", "count": 1650, "color": "#ef4444", "percent": 1.1},
        ],
        "transactionTypes": [
            {"type": "P2P (Peer to Peer)", "safe": 65400, "suspicious": 1890, "stopReview": 740, "total": 68030},
            {"type": "P2M (Merchant Pay)", "safe": 52100, "suspicious": 920, "stopReview": 210, "total": 53230},
            {"type": "Collect Request", "safe": 11400, "suspicious": 1680, "stopReview": 580, "total": 13660},
            {"type": "QR Scan", "safe": 9800, "suspicious": 320, "stopReview": 90, "total": 10210},
            {"type": "Bill Payments (BBPS)", "safe": 3680, "suspicious": 80, "stopReview": 30, "total": 3790},
        ],
        "transactionTypesVolume": [
            {"type": "P2P (Peer to Peer)", "safe": 65400, "suspicious": 1890, "stopReview": 740, "total": 68030},
            {"type": "P2M (Merchant Pay)", "safe": 52100, "suspicious": 920, "stopReview": 210, "total": 53230},
            {"type": "Collect Request", "safe": 11400, "suspicious": 1680, "stopReview": 580, "total": 13660},
            {"type": "QR Scan", "safe": 9800, "suspicious": 320, "stopReview": 90, "total": 10210},
            {"type": "Bill Payments (BBPS)", "safe": 3680, "suspicious": 80, "stopReview": 30, "total": 3790},
        ],
        "hourlyTraffic": [
            {"hour": "00:00", "volume": 1200, "riskAssessments": 45},
            {"hour": "04:00", "volume": 420, "riskAssessments": 52},
            {"hour": "08:00", "volume": 4800, "riskAssessments": 32},
            {"hour": "12:00", "volume": 11400, "riskAssessments": 95},
            {"hour": "16:00", "volume": 10600, "riskAssessments": 112},
            {"hour": "20:00", "volume": 14200, "riskAssessments": 124},
        ],
    }


@router.get("/fraud/analytics")
def api_v1_get_stored_fraud_analytics(
    dateRange: str = Query("7D", pattern="^(24H|7D|30D)$"),
    txnType: str = Query("ALL"),
    db: Session = Depends(get_db),
):
    """Aggregate only stored local transaction and assessment records."""
    return get_analytics(db, date_range=dateRange, txn_type=txnType)


# ---------------------------------------------------------------------------
# 6. Screenshot & Evidence OCR Analysis
# ---------------------------------------------------------------------------
@router.post("/fraud/screenshot-ocr")
async def api_v1_screenshot_ocr(
    image: Optional[UploadFile] = File(None),
    sample_key: Optional[str] = Form(None),
):
    """Return a labeled sample only; uploaded-image OCR is not implemented."""
    if sample_key != "scan-sample-2":
        raise AppError(
            ErrorCode.BAD_REQUEST,
            "Image OCR is unavailable. Only the explicitly labeled demo sample is supported.",
            status_code=501,
        )

    # Preset sample check
    if sample_key == "scan-sample-2":
        return {
            "success": True,
            "data_label": "DEMO DATA — sample response, image not analyzed",
            "simulated": True,
            "data": {
                "id": "scan-sample-2",
                "filename": "electricity_power_cut_warning.jpg",
                "verdict": "BILL PAYMENT EXTORTION / FRAUDULENT VPA",
                "riskScore": 94,
                "riskCategory": "HIGH",
                "summary": "High-urgency fear-appeal phishing message. Utilities do not send disconnect notices via generic personal UPI handles.",
                "ocrExtractedText": "Dear Consumer, your electricity power will be disconnected tonight at 9:30 PM from power office because your previous month bill was not updated. Please immediately contact our electricity officer Mr. Sharma at 9876543210 or pay via UPI: discom-bill-sbi@okhdfcbank",
                "extractedEntities": {
                    "suspiciousUpiIds": ["discom-bill-sbi@okhdfcbank"],
                    "flaggedKeywords": ["power will be disconnected", "tonight at 9:30 PM", "bill was not updated", "contact officer"],
                    "detectedAmount": "₹3,450.00",
                    "claimedSender": "State Electricity Board (Spoofed)",
                    "qrCodePresent": False,
                    "qrPayload": None,
                },
                "forensicFindings": [
                    {
                        "rule": "OCR-04: Utility Disconnection Coercion",
                        "severity": "HIGH",
                        "detail": "Genuine electricity distribution companies operate strictly via Bharat BillPay (BBPS) or registered merchant portals, not personal VPA handles.",
                    },
                    {
                        "rule": "OCR-05: Private Phone Contact as Official Support",
                        "severity": "HIGH",
                        "detail": "Standard scam vector urging direct phone calls to extract OTPs or initiate screen sharing (AnyDesk/TeamViewer).",
                    },
                ],
                "safetyAction": "Do NOT transfer funds or call the number provided. Verify bill status strictly via official state electricity DISCOM portal.",
            },
        }

    # Default / Sample 1 / File Upload analysis
    filename = image.filename if image else "cashback_scratchcard_win_₹4999.png"
    return {
        "success": True,
        "data_label": "DEMO DATA — sample response, image not analyzed",
        "simulated": True,
        "data": {
            "id": sample_key or "scan-live-01",
            "filename": filename,
            "verdict": "MALICIOUS PHISHING & REVERSE DEBIT SCAM",
            "riskScore": 97,
            "riskCategory": "HIGH",
            "summary": "This image contains high-probability deceptive social engineering tactics designed to entice the victim into authorizing a collect request or sending money under the guise of 'claiming cashback'.",
            "ocrExtractedText": "CONGRATULATIONS! You have won ₹4,999 Cashback in PhonePe Festive Rewards! Send payment request of ₹1 to verify bank account and receive ₹4,999 directly into your Google Pay/PhonePe. Pay to claim: reward-win-claim@ybl",
            "extractedEntities": {
                "suspiciousUpiIds": ["reward-win-claim@ybl", "fastreward2026@icici"],
                "flaggedKeywords": ["won ₹4,999 Cashback", "Festive Rewards", "Send payment request of ₹1", "Pay to claim"],
                "detectedAmount": "₹4,999.00",
                "claimedSender": "PhonePe Festive Rewards (Spoofed)",
                "qrCodePresent": True,
                "qrPayload": "upi://pay?pa=reward-win-claim@ybl&pn=FestiveRewards&am=4999.00&cu=INR",
            },
            "forensicFindings": [
                {
                    "rule": "OCR-01: Cashback Advance Payment Lure",
                    "severity": "HIGH",
                    "detail": "NPCI and banks NEVER require users to send money or approve a request to receive rewards or cashback.",
                },
                {
                    "rule": "OCR-02: Embedded QR Code Payload Anomaly",
                    "severity": "HIGH",
                    "detail": "The QR code decodes to a direct payment debit of ₹4,999 instead of a credit transfer.",
                },
                {
                    "rule": "OCR-03: Typosquatted Brand Identity",
                    "severity": "HIGH",
                    "detail": "Graphic overlays imitate PhonePe brand assets without valid cryptographic signature or domain certification.",
                },
            ],
            "safetyAction": "Do NOT scan QR code or enter your UPI PIN. Immediately report this handle to National Cyber Crime Portal (1930).",
        },
    }


# ---------------------------------------------------------------------------
# 7. Fraud Alerts & Threat Dossiers
# ---------------------------------------------------------------------------
@router.get("/demo/fraud/alerts", deprecated=True)
def api_v1_get_demo_fraud_alerts():
    """Explicitly marked legacy synthetic alert examples."""
    items = [dict(alert, data_label="DEMO DATA") for alert in DEFAULT_ALERTS]
    return {
        "success": True,
        "total": len(items),
        "data_label": "DEMO DATA — synthetic examples, not live alerts",
        "summary": {"criticalHighAlerts": 0, "mediumAlerts": 0},
        "data": items,
    }


@router.get("/fraud/alerts")
def api_v1_get_stored_fraud_alerts(db: Session = Depends(get_db)):
    """Build alert dossiers from persisted medium/high risk assessments only."""
    assessments = (
        db.query(models.RiskAssessment)
        .filter(models.RiskAssessment.category.in_(["MEDIUM", "HIGH"]))
        .order_by(desc(models.RiskAssessment.created_at))
        .all()
    )
    resolutions = {
        resolution.assessment_id: resolution
        for resolution in db.query(models.RiskAssessmentResolution).all()
    }
    transactions = {
        tx.transaction_id: tx
        for tx in db.query(models.Transaction).all()
    }
    items = []
    for assessment in assessments:
        tx = transactions.get(assessment.transaction_id)
        if tx is None:
            continue
        reasons = [
            reason["text"]
            for reason in (assessment.reasons or [])
            if isinstance(reason, dict) and reason.get("text")
        ]
        resolution = resolutions.get(assessment.assessment_id)
        items.append({
            "id": assessment.assessment_id,
            "severity": assessment.category,
            "category": assessment.category,
            "riskScore": assessment.score,
            "title": f"{assessment.category.title()} risk assessment",
            "detectedAt": assessment.created_at,
            "affectedAccount": tx.sender_id,
            "suspectEntity": tx.receiver_id,
            "amount": tx.amount,
            "status": resolution.status if resolution else "OPEN",
            "ruleBroken": "Rule-based heuristic assessment",
            "explanation": (
                "PayShield recorded this internal risk assessment. It is not proof of fraud "
                "and did not block or execute a payment."
            ),
            "indicators": reasons,
            "recommendedActions": [
                "Review the recorded assessment before making an independent payment decision."
            ],
            "resolutionNotes": resolution.notes if resolution else None,
        })

    high_count = sum(item["category"] == "HIGH" for item in items)
    medium_count = sum(item["category"] == "MEDIUM" for item in items)
    resolved_count = sum(item["status"] == "RESOLVED" for item in items)
    return {
        "success": True,
        "total": len(items),
        "summary": {
            "totalAlerts": len(items),
            "highRiskAssessments": high_count,
            "mediumRiskAssessments": medium_count,
            "resolvedAssessments": resolved_count,
            "fraudPreventedAmount": None,
            "payment_provider_integration": False,
        },
        "data_label": "DEMO / SYNTHETIC DATA",
        "simulated": True,
        "data": items,
    }


@router.post("/fraud/alerts/{alert_id}/resolve")
def api_v1_resolve_alert(
    alert_id: str,
    body: AlertResolveRequest,
    db: Session = Depends(get_db),
):
    """Persist a resolution note for a stored risk assessment."""
    assessment = db.get(models.RiskAssessment, alert_id)
    if assessment is None:
        raise AppError(ErrorCode.NOT_FOUND, "Stored risk assessment not found", status_code=404)
    resolution = models.RiskAssessmentResolution(
        assessment_id=alert_id,
        status="RESOLVED",
        notes=body.notes or "",
        updated_at=datetime.now(timezone.utc).isoformat(),
    )
    db.merge(resolution)
    db.commit()
    return {
        "success": True,
        "alert_id": alert_id,
        "status": "RESOLVED",
        "message": f"Stored assessment {alert_id} marked as resolved.",
    }
