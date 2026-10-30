"""SQLAlchemy ORM models – 9 tables for PayShield AI.

Tables:
    1. demo_users
    2. transactions
    3. risk_assessments
    4. accounts_or_vpas
    5. fraud_intelligence
    6. graph_edges
    7. merchant_sessions
    8. payment_events
    9. grievances
"""

from __future__ import annotations

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    ForeignKey,
    JSON,
    DateTime,
)
from sqlalchemy.sql import func

from app.database import Base


class DemoUser(Base):
    __tablename__ = "demo_users"

    user_id = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    baseline_profile = Column(JSON, nullable=False, default=dict)
    # baseline_profile schema:
    # {
    #   "avg_amount": float,
    #   "max_amount": float,
    #   "txn_per_week": int,
    #   "usual_hours": [start: int, end: int],
    #   "known_recipients": [str, ...]
    # }


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String, primary_key=True)
    sender_id = Column(String, nullable=False)
    receiver_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    timestamp = Column(String, nullable=False)  # ISO 8601 UTC
    status = Column(String, nullable=False, default="PENDING")  # PENDING|COMPLETED|FLAGGED
    request_type = Column(String, nullable=False, default="PAY")  # PAY|COLLECT_REQUEST
    session_id = Column(String, nullable=True)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    assessment_id = Column(String, primary_key=True)
    transaction_id = Column(String, ForeignKey("transactions.transaction_id"), nullable=False)
    score = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    reasons = Column(JSON, nullable=False, default=list)
    recommended_action = Column(String, nullable=False)
    playbook_matches = Column(JSON, nullable=False, default=list)
    model_version = Column(String, nullable=False)
    created_at = Column(String, nullable=False)


class AccountOrVPA(Base):
    __tablename__ = "accounts_or_vpas"

    account_id = Column(String, primary_key=True)
    vpa = Column(String, nullable=True)
    mobile = Column(String, nullable=True)
    created_at_if_known = Column(String, nullable=True)
    report_status = Column(String, nullable=False, default="NONE")  # NONE|REPORTED|VERIFIED
    risk_context = Column(JSON, nullable=False, default=dict)


class FraudIntelligence(Base):
    __tablename__ = "fraud_intelligence"

    indicator_id = Column(String, primary_key=True)
    indicator_type = Column(String, nullable=False)  # VPA|MOBILE|URL|DOMAIN
    indicator_value = Column(String, nullable=False)
    source = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    review_status = Column(String, nullable=False, default="UNREVIEWED")
    # UNREVIEWED|VERIFIED|DISPUTED|RETRACTED
    reported_at = Column(String, nullable=False)
    reviewed_at = Column(String, nullable=True)


class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_account = Column(String, nullable=False)
    target_account = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    timestamp = Column(String, nullable=False)
    transaction_id = Column(String, nullable=True)


class MerchantSession(Base):
    __tablename__ = "merchant_sessions"

    session_id = Column(String, primary_key=True)
    merchant_id = Column(String, nullable=False)
    expected_amount = Column(Float, nullable=False)
    created_at = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PENDING")


class PaymentEvent(Base):
    __tablename__ = "payment_events"

    event_id = Column(String, primary_key=True)
    session_id = Column(String, nullable=False)
    provider_reference = Column(String, nullable=True)
    status = Column(String, nullable=False)
    simulated = Column(Boolean, nullable=False, default=True)
    verified_at = Column(String, nullable=True)


class Grievance(Base):
    __tablename__ = "grievances"

    case_id = Column(String, primary_key=True)
    user_reference = Column(String, nullable=False)
    assessment_id = Column(String, ForeignKey("risk_assessments.assessment_id"), nullable=False)
    reason = Column(Text, nullable=False)
    evidence_ref = Column(String, nullable=True)
    status = Column(String, nullable=False, default="SUBMITTED")
    # SUBMITTED|UNDER_REVIEW|MORE_INFO_REQUIRED|RESOLVED|REJECTED
    reviewer_note = Column(Text, nullable=True)
    status_history = Column(JSON, nullable=False, default=list)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)
