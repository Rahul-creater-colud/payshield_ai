"""Score combination and final risk categorisation.

Combines all layer results into a single score, category, and action.
The ML teammate can add an ml_adjustment() hook here.

Thresholds (from config):
- LOW:    0-39  -> PROCEED
- MEDIUM: 40-69 -> CAUTION_VERIFY
- HIGH:   70-100 -> STOP_AND_REVIEW
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.config import settings


def ml_adjustment(ctx: Dict[str, Any]) -> Optional[int]:
    """Keep experimental ML output separate from the heuristic risk score.

    The current model is trained on generated labels and is not validated
    for use in the final risk decision.

    Args:
        ctx: Full RiskContext dict.

    Returns:
        None until a validated model is approved to affect final decisions.
    """
    return None


def combine(
    behaviour_result,
    graph_result,
    playbook_matches: list,
    intel_score: int,
    intel_reasons: list,
    url_result: Optional[dict],
    ctx: Dict[str, Any],
) -> Tuple[int, str, List[dict], str]:
    """Combine all risk layers into final score, category, reasons and action.

    Args:
        behaviour_result: LayerResult from behaviour.evaluate_behaviour()
        graph_result: LayerResult from graph_layer.evaluate_graph()
        playbook_matches: list of PlaybookMatch from playbooks.match_playbooks()
        intel_score: intelligence layer score
        intel_reasons: intelligence layer reasons
        url_result: dict with url scan results (score, reasons) or None
        ctx: full RiskContext for ML hook

    Returns:
        Tuple of (score, category, all_reasons, recommended_action)
    """
    all_reasons = []
    layer_scores = {
        "behaviour": behaviour_result.score,
        "graph": graph_result.score,
        "playbook": 0,
        "intelligence": intel_score,
    }

    # Collect behaviour reasons
    all_reasons.extend(behaviour_result.reasons)

    # Collect graph reasons
    all_reasons.extend(graph_result.reasons)

    # Playbook contributions
    playbook_score = 0
    for pm in playbook_matches:
        playbook_score += pm.score_contribution
        all_reasons.append({
            "code": f"PLAYBOOK_{pm.name}",
            "layer": "playbook",
            "text": pm.warning,
            "weight": pm.score_contribution,
        })
    layer_scores["playbook"] = min(playbook_score, 100)

    # Intelligence reasons
    all_reasons.extend(intel_reasons)

    # URL reasons
    url_score = 0
    if url_result:
        url_score = url_result.get("score", 0)
        for r in url_result.get("reasons", []):
            all_reasons.append(r)

    # Weighted combination
    weighted = (
        behaviour_result.score * 0.25
        + graph_result.score * 0.25
        + min(playbook_score, 100) * 0.25
        + intel_score * 0.20
        + url_score * 0.05
    )

    # Specific threat signals should not be diluted when critical patterns match
    threat_floor = 0
    if playbook_score > 0:
        threat_floor = max(threat_floor, min(playbook_score + (intel_score // 2), 90))
    if graph_result.score >= 35:
        threat_floor = max(threat_floor, graph_result.score)
    if intel_score >= 40:
        threat_floor = max(threat_floor, intel_score)

    raw_score = max(weighted, threat_floor)
    score = int(min(max(round(raw_score), 0), 100))

    # New recipient alone must never produce HIGH
    reasons_codes = [r.get("code") for r in all_reasons]
    if (
        reasons_codes == ["NEW_RECIPIENT"]
        or (set(reasons_codes) <= {"NEW_RECIPIENT", "UNUSUAL_HOUR"})
    ):
        score = min(score, settings.THRESHOLD_MEDIUM_MAX)

    # ML adjustment hook
    adj = ml_adjustment(ctx)
    if adj is not None:
        score = int(min(max(score + adj, 0), 100))

    # Categorise
    if score <= settings.THRESHOLD_LOW_MAX:
        category = "LOW"
        action = "PROCEED"
    elif score <= settings.THRESHOLD_MEDIUM_MAX:
        category = "MEDIUM"
        action = "CAUTION_VERIFY"
    else:
        category = "HIGH"
        action = "STOP_AND_REVIEW"

    # Sort reasons by weight descending
    all_reasons.sort(key=lambda r: r.get("weight", 0), reverse=True)

    return score, category, all_reasons, action
