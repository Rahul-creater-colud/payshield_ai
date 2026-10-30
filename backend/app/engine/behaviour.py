"""Behavioural analysis layer – compares transaction against user baseline.

The ML teammate can replace the internals of evaluate_behaviour() without
touching routers or schemas. Keep the signature and return type stable.

Default rules (illustrative heuristics, NOT proof of fraud):
- Amount vs avg/max baseline
- New recipient detection
- Unusual hour detection
- Velocity check (transactions in last hour)
- New recipient ALONE adds only a small weight (never exceeds MEDIUM by itself)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class LayerResult:
    """Standard return type for every risk layer."""
    score: int  # 0-100 contribution
    reasons: list  # list of dicts with code, layer, text, weight
    flags: list  # additional flags/metadata


def evaluate_behaviour(ctx: Dict[str, Any]) -> LayerResult:
    """Evaluate a transaction against the sender's baseline profile.

    Args:
        ctx: RiskContext dict containing:
            - sender_baseline: dict with avg_amount, max_amount, txn_per_week,
              usual_hours, known_recipients
            - amount: float
            - receiver_id: str
            - hour: int (0-23 UTC)
            - request_type: str (PAY|COLLECT_REQUEST)
            - recent_txn_count: int (transactions in last hour)
            - message_text: optional str
            - unsolicited: bool

    Returns:
        LayerResult with behaviour score (0-100) and reasons.
    """
    score = 0
    reasons = []
    flags = []

    baseline = ctx.get("sender_baseline") or {}
    amount = ctx.get("amount", 0)
    receiver_id = ctx.get("receiver_id", "")
    hour = ctx.get("hour", 12)
    request_type = ctx.get("request_type", "PAY")
    recent_txn_count = ctx.get("recent_txn_count", 0)
    known_recipients = baseline.get("known_recipients", [])
    avg_amount = baseline.get("avg_amount", 1000)
    max_amount = baseline.get("max_amount", 5000)
    usual_hours = baseline.get("usual_hours", [8, 22])

    # 1. Amount deviation
    if max_amount > 0 and amount > max_amount * 2:
        weight = 20
        score += weight
        reasons.append({
            "code": "AMOUNT_FAR_EXCEEDS_MAX",
            "layer": "behaviour",
            "text": f"Amount ({amount}) is more than 2x your usual maximum ({max_amount}).",
            "weight": weight,
        })
    elif max_amount > 0 and amount > max_amount:
        weight = 12
        score += weight
        reasons.append({
            "code": "AMOUNT_EXCEEDS_MAX",
            "layer": "behaviour",
            "text": f"Amount ({amount}) exceeds your usual maximum ({max_amount}).",
            "weight": weight,
        })
    elif avg_amount > 0 and amount > avg_amount * 3:
        weight = 10
        score += weight
        reasons.append({
            "code": "AMOUNT_HIGH_VS_AVG",
            "layer": "behaviour",
            "text": f"Amount ({amount}) is significantly higher than your average ({avg_amount}).",
            "weight": weight,
        })

    # 2. New recipient (small weight alone – never exceeds MEDIUM by itself)
    if receiver_id and receiver_id not in known_recipients:
        weight = 8
        score += weight
        reasons.append({
            "code": "NEW_RECIPIENT",
            "layer": "behaviour",
            "text": "Sending to a recipient not in your usual list.",
            "weight": weight,
        })
        flags.append("NEW_RECIPIENT")

    # 3. Unusual hour
    start_h, end_h = usual_hours[0], usual_hours[1]
    if start_h <= end_h:
        outside = hour < start_h or hour > end_h
    else:
        outside = hour < start_h and hour > end_h
    if outside:
        weight = 10
        score += weight
        reasons.append({
            "code": "UNUSUAL_HOUR",
            "layer": "behaviour",
            "text": f"Transaction initiated at an unusual hour ({hour}:00 UTC).",
            "weight": weight,
        })

    # 4. Velocity (many transactions in last hour)
    if recent_txn_count > 5:
        weight = 15
        score += weight
        reasons.append({
            "code": "HIGH_VELOCITY",
            "layer": "behaviour",
            "text": f"You have made {recent_txn_count} transactions in the last hour, which is unusually high.",
            "weight": weight,
        })
    elif recent_txn_count > 3:
        weight = 8
        score += weight
        reasons.append({
            "code": "ELEVATED_VELOCITY",
            "layer": "behaviour",
            "text": f"You have made {recent_txn_count} transactions in the last hour.",
            "weight": weight,
        })

    # 5. Collect request
    if request_type == "COLLECT_REQUEST":
        weight = 15
        score += weight
        reasons.append({
            "code": "COLLECT_REQUEST",
            "layer": "behaviour",
            "text": "This is a collect request - money will be debited, not credited.",
            "weight": weight,
        })

    # 6. Unsolicited
    if ctx.get("unsolicited"):
        weight = 10
        score += weight
        reasons.append({
            "code": "UNSOLICITED",
            "layer": "behaviour",
            "text": "This transaction was initiated without your request.",
            "weight": weight,
        })

    # Cap at 100
    score = min(score, 100)

    return LayerResult(score=score, reasons=reasons, flags=flags)
