"""Risk assessment orchestration – the heart of PayShield AI.

Flow:
  1. Validate sender + load baseline; load receiver record (None → new).
  2. Build RiskContext dict.
  3. Call engine layers: behaviour, graph, playbooks, url, intelligence.
  4. Combine → score/category/reasons/action.
  5. Persist transaction + risk_assessment rows.
  6. Return structured RiskAssessResponse.

The engine/* modules have stable typed signatures so the ML teammate can
replace internals without touching this file.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy.orm import Session

from app.config import settings
from app.errors import AppError, ErrorCode
from app.models import (
    DemoUser,
    AccountOrVPA,
    Transaction,
    RiskAssessment,
    GraphEdge,
    MLModelResult,
)
from app.schemas import RiskAssessRequest

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


def assess(db: Session, req: RiskAssessRequest) -> Dict[str, Any]:
    """Full risk assessment pipeline.

    Args:
        db: SQLAlchemy session.
        req: Validated RiskAssessRequest.

    Returns:
        Dict matching RiskAssessResponse schema.
    """
    # ------------------------------------------------------------------
    # 1. Validate sender
    # ------------------------------------------------------------------
    sender: Optional[DemoUser] = db.get(DemoUser, req.sender_id)
    if sender is None:
        raise AppError(ErrorCode.NOT_FOUND, f"Sender '{req.sender_id}' not found.", 404)

    # ------------------------------------------------------------------
    # 2. Load receiver (None → unknown / new recipient)
    # ------------------------------------------------------------------
    receiver: Optional[AccountOrVPA] = db.get(AccountOrVPA, req.receiver_id)

    # ------------------------------------------------------------------
    # 3. Build RiskContext
    # ------------------------------------------------------------------
    ctx_timestamp = req.timestamp or datetime.now(timezone.utc).isoformat()
    try:
        ts = datetime.fromisoformat(ctx_timestamp.replace("Z", "+00:00"))
    except ValueError:
        ts = datetime.now(timezone.utc)

    hour = ts.hour

    # Velocity: sender's transactions in last hour
    one_hour_ago = (ts - timedelta(hours=1)).isoformat()
    recent_txns = (
        db.query(Transaction)
        .filter(
            Transaction.sender_id == req.sender_id,
            Transaction.timestamp >= one_hour_ago,
        )
        .all()
    )
    recent_txn_count = len(recent_txns)

    # Sender history with this receiver
    history = (
        db.query(Transaction)
        .filter(
            Transaction.sender_id == req.sender_id,
            Transaction.receiver_id == req.receiver_id,
        )
        .all()
    )

    ctx_obj = req.context
    ctx: Dict[str, Any] = {
        "sender_id": req.sender_id,
        "receiver_id": req.receiver_id,
        "amount": req.amount,
        "request_type": req.request_type,
        "hour": hour,
        "timestamp": ctx_timestamp,
        "recent_txn_count": recent_txn_count,
        "sender_baseline": sender.baseline_profile or {},
        "receiver": receiver,
        "history_with_receiver": history,
        "message_text": ctx_obj.message_text if ctx_obj else None,
        "url": ctx_obj.url if ctx_obj else None,
        "unsolicited": ctx_obj.unsolicited if ctx_obj else False,
        "events": ctx_obj.events if ctx_obj else [],
        "graph_features": {},
        "intel_hits": [],
    }
    sender_transactions = (
        db.query(Transaction)
        .filter(Transaction.sender_id == req.sender_id)
        .all()
    )
    model_features, model_assumptions = build_transaction_features(
        req.amount,
        ts,
        sender_transactions,
        req.receiver_id,
    )
    ml_assessment = ml_model_service.predict(
        model_features, model_assumptions
    )

    # ------------------------------------------------------------------
    # 4. Graph features
    # ------------------------------------------------------------------
    ctx["graph_features"] = graph_service.get_graph_features(db, req.receiver_id)

    # ------------------------------------------------------------------
    # 5. Intelligence lookup
    # ------------------------------------------------------------------
    intel_score, intel_reasons = intelligence_service.get_intel_for_risk(
        db, req.receiver_id,
        vpa=receiver.vpa if receiver else None,
        mobile=receiver.mobile if receiver else None,
    )

    # ------------------------------------------------------------------
    # 6. Engine layers
    # ------------------------------------------------------------------
    beh_result = behaviour_engine.evaluate_behaviour(ctx)
    grph_result = graph_engine.evaluate_graph(ctx)
    pb_matches = playbook_engine.match_playbooks(ctx)

    # URL scan (if URL provided)
    url_result: Optional[dict] = None
    if ctx.get("url"):
        raw_scan = url_service.scan_url(ctx["url"], db=db)
        url_result = {
            "score": raw_scan["risk_score"],
            "reasons": [
                {
                    "code": ind["code"],
                    "layer": "url",
                    "text": ind["text"],
                    "weight": 5,
                }
                for ind in raw_scan.get("indicators", [])
                if ind["code"] != "HTTPS_NOTE"
            ],
        }

    # ------------------------------------------------------------------
    # 7. Combine scores
    # ------------------------------------------------------------------
    score, category, all_reasons, action = scoring_engine.combine(
        beh_result, grph_result, pb_matches,
        intel_score, intel_reasons, url_result, ctx,
    )

    # ------------------------------------------------------------------
    # 8. Safety warnings
    # ------------------------------------------------------------------
    safety_warnings: List[str] = []
    if category == "HIGH":
        safety_warnings.append(
            "High fraud risk detected. Do NOT proceed without careful verification."
        )
    if category == "MEDIUM":
        safety_warnings.append(
            "Please verify the recipient and purpose before proceeding."
        )
    if req.request_type == "COLLECT_REQUEST":
        safety_warnings.append(
            "This is a COLLECT REQUEST – approving it will DEBIT your account."
        )

    # ------------------------------------------------------------------
    # 9. Build structured output objects
    # ------------------------------------------------------------------
    collect_request_warning: Optional[str] = None
    if req.request_type == "COLLECT_REQUEST":
        collect_request_warning = (
            "This is a payment REQUEST. Approving it may DEBIT your account, not credit it."
        )

    # Playbook matches → schema dicts
    pb_dicts = [
        {
            "playbook_id": pm.playbook_id,
            "name": pm.name,
            "warning": pm.warning,
            "recommended_action": pm.recommended_action,
        }
        for pm in pb_matches
    ]

    # Graph flags from graph_result
    graph_flags: List[Dict[str, Any]] = [
        f for f in (grph_result.flags or []) if isinstance(f, dict)
    ]

    layer_scores = {
        "behaviour": beh_result.score,
        "graph": grph_result.score,
        "playbook": min(sum(pm.score_contribution for pm in pb_matches), 100),
        "intelligence": intel_score,
    }

    # Reason dicts → ensure all required fields
    reason_dicts = [
        {
            "code": r.get("code", "UNKNOWN"),
            "layer": r.get("layer", "behaviour"),
            "text": r.get("text", ""),
            "weight": r.get("weight", 0),
        }
        for r in all_reasons
    ]

    # ------------------------------------------------------------------
    # 10. Persist
    # ------------------------------------------------------------------
    now_str = datetime.now(timezone.utc).isoformat()
    txn_id = f"TXN_{uuid.uuid4().hex[:6].upper()}"
    asm_id = f"ASM_{uuid.uuid4().hex[:6].upper()}"
    txn_status = "FLAGGED" if category == "HIGH" else "PENDING"

    txn = Transaction(
        transaction_id=txn_id,
        sender_id=req.sender_id,
        receiver_id=req.receiver_id,
        amount=req.amount,
        timestamp=ctx_timestamp,
        status=txn_status,
        request_type=req.request_type,
        session_id=None,
    )
    db.add(txn)
    db.add(GraphEdge(
        source_account=req.sender_id,
        target_account=req.receiver_id,
        amount=req.amount,
        timestamp=ctx_timestamp,
        transaction_id=txn_id,
    ))

    asm = RiskAssessment(
        assessment_id=asm_id,
        transaction_id=txn_id,
        score=score,
        category=category,
        reasons=reason_dicts,
        recommended_action=action,
        playbook_matches=pb_dicts,
        model_version=settings.MODEL_VERSION,
        created_at=now_str,
    )
    db.add(asm)
    db.add(MLModelResult(
        assessment_id=asm_id,
        status=ml_assessment["status"],
        model_name=ml_assessment["model_name"],
        training_data=ml_assessment["training_data"],
        affects_final_score=ml_assessment["affects_final_score"],
        message=ml_assessment["message"],
        probability=ml_assessment["probability"],
        threshold=ml_assessment["threshold"],
        prediction=ml_assessment["prediction"],
        feature_assumptions=ml_assessment["feature_assumptions"],
        calculated_at=now_str,
    ))
    db.commit()

    # ------------------------------------------------------------------
    # 11. Generate LLM Risk Explanation
    # ------------------------------------------------------------------
    llm_explanation = llm_service.generate_explanation(
        transaction_data={
            "sender_upi": req.sender_id,
            "receiver_upi": req.receiver_id,
            "amount": req.amount,
            "transaction_type": req.request_type,
            "timestamp": ctx_timestamp,
        },
        risk_assessment={
            "score": score,
            "category": category,
            "reasons": reason_dicts,
            "action": action,
        },
    )

    # ------------------------------------------------------------------
    # 12. Return response dict
    # ------------------------------------------------------------------
    return {
        "assessment_id": asm_id,
        "transaction_id": txn_id,
        "score": score,
        "category": category,
        "reasons": reason_dicts,
        "recommended_action": action,
        "safety_warnings": safety_warnings,
        "playbook_matches": pb_dicts,
        "graph_flags": graph_flags,
        "layer_scores": layer_scores,
        "collect_request_warning": collect_request_warning,
        "llm_explanation": llm_explanation,
        "ml_model": ml_assessment,
        "model_version": settings.MODEL_VERSION,
        "simulated": True,
        "disclaimer": settings.DISCLAIMER,
    }


def get_assessment(db: Session, assessment_id: str) -> Dict[str, Any]:
    """Retrieve a stored risk assessment by ID."""
    asm: Optional[RiskAssessment] = db.get(RiskAssessment, assessment_id)
    if asm is None:
        raise AppError(ErrorCode.NOT_FOUND, f"Assessment {assessment_id} not found.", 404)

    txn: Optional[Transaction] = db.get(Transaction, asm.transaction_id)
    request_type = txn.request_type if txn else "PAY"
    collect_warn = (
        "This is a payment REQUEST. Approving it may DEBIT your account, not credit it."
        if request_type == "COLLECT_REQUEST" else None
    )

    reasons = asm.reasons or []
    pb_matches = asm.playbook_matches or []

    return {
        "assessment_id": asm.assessment_id,
        "transaction_id": asm.transaction_id,
        "score": asm.score,
        "category": asm.category,
        "reasons": reasons,
        "recommended_action": asm.recommended_action,
        "safety_warnings": [],
        "playbook_matches": pb_matches,
        "graph_flags": [],
        "layer_scores": {"behaviour": 0, "graph": 0, "playbook": 0, "intelligence": 0},
        "collect_request_warning": collect_warn,
        "model_version": asm.model_version,
        "ml_model": _stored_ml_model(db, asm.assessment_id),
        "simulated": True,
        "disclaimer": settings.DISCLAIMER,
    }


def list_assessments(db: Session, limit: int = 20) -> List[Dict[str, Any]]:
    """Return recent assessments (summary list)."""
    rows = (
        db.query(RiskAssessment)
        .order_by(RiskAssessment.created_at.desc())
        .limit(limit)
        .all()
    )
    results = []
    for asm in rows:
        txn: Optional[Transaction] = db.get(Transaction, asm.transaction_id)
        request_type = txn.request_type if txn else "PAY"
        collect_warn = (
            "This is a payment REQUEST. Approving it may DEBIT your account, not credit it."
            if request_type == "COLLECT_REQUEST" else None
        )
        results.append({
            "assessment_id": asm.assessment_id,
            "transaction_id": asm.transaction_id,
            "score": asm.score,
            "category": asm.category,
            "reasons": asm.reasons or [],
            "recommended_action": asm.recommended_action,
            "safety_warnings": [],
            "playbook_matches": asm.playbook_matches or [],
            "graph_flags": [],
            "layer_scores": {"behaviour": 0, "graph": 0, "playbook": 0, "intelligence": 0},
            "collect_request_warning": collect_warn,
            "model_version": asm.model_version,
            "ml_model": _stored_ml_model(db, asm.assessment_id),
            "simulated": True,
            "disclaimer": settings.DISCLAIMER,
        })
    return results


def _stored_ml_model(db: Session, assessment_id: str) -> Optional[Dict[str, Any]]:
    result: Optional[MLModelResult] = db.get(MLModelResult, assessment_id)
    if result is None:
        return None
    return {
        "status": result.status,
        "model_name": result.model_name,
        "training_data": result.training_data,
        "affects_final_score": result.affects_final_score,
        "message": result.message,
        "probability": result.probability,
        "threshold": result.threshold,
        "prediction": result.prediction,
        "feature_assumptions": result.feature_assumptions or [],
    }
