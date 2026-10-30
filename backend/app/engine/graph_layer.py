"""Graph analysis layer – detects suspicious network patterns.

Uses precomputed graph features from graph_service. The ML teammate can
replace internals without touching routers or schemas.

Default rules (illustrative heuristics):
- Fan-in (>=4 distinct senders to one account)
- Fan-out (>=3 distinct recipients from one account)
- Rapid onward transfer (forwarding within 15 min)
- Multi-hop path detection
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class LayerResult:
    """Standard return type for every risk layer."""
    score: int
    reasons: list
    flags: list


def evaluate_graph(ctx: Dict[str, Any]) -> LayerResult:
    """Evaluate graph-based risk for the receiver account.

    Args:
        ctx: RiskContext dict containing:
            - graph_features: dict with keys:
                - fan_in_count: int
                - fan_out_count: int
                - rapid_onward: bool
                - multi_hop_paths: list
                - fan_in_accounts: list[str]
                - fan_out_accounts: list[str]
            - receiver_id: str

    Returns:
        LayerResult with graph score and reasons.
    """
    score = 0
    reasons = []
    flags = []

    gf = ctx.get("graph_features") or {}
    receiver_id = ctx.get("receiver_id", "")

    fan_in = gf.get("fan_in_count", 0)
    fan_out = gf.get("fan_out_count", 0)
    rapid_onward = gf.get("rapid_onward", False)
    multi_hop = gf.get("multi_hop_paths", [])
    fan_in_accounts = gf.get("fan_in_accounts", [])
    fan_out_accounts = gf.get("fan_out_accounts", [])

    # Fan-in detection
    if fan_in >= 4:
        weight = 20
        score += weight
        reasons.append({
            "code": "FAN_IN",
            "layer": "graph",
            "text": (
                f"The recipient ({receiver_id}) has received funds from "
                f"{fan_in} distinct senders recently. This pattern is sometimes "
                f"associated with money collection schemes, but is not proof of wrongdoing."
            ),
            "weight": weight,
        })
        flags.append({"pattern": "FAN_IN", "accounts": fan_in_accounts,
                       "explanation": f"Account {receiver_id} received from {fan_in} distinct senders. "
                       "A graph connection is an indicator, NOT proof of wrongdoing."})

    # Fan-out detection
    if fan_out >= 3:
        weight = 18
        score += weight
        reasons.append({
            "code": "FAN_OUT",
            "layer": "graph",
            "text": (
                f"The recipient ({receiver_id}) has sent funds to "
                f"{fan_out} distinct accounts recently. Rapid distribution "
                f"is an indicator worth noting, but is not proof of wrongdoing."
            ),
            "weight": weight,
        })
        flags.append({"pattern": "FAN_OUT", "accounts": fan_out_accounts,
                       "explanation": f"Account {receiver_id} sent to {fan_out} distinct accounts. "
                       "A graph connection is an indicator, NOT proof of wrongdoing."})

    # Rapid onward transfer
    if rapid_onward:
        weight = 15
        score += weight
        reasons.append({
            "code": "RAPID_ONWARD",
            "layer": "graph",
            "text": (
                f"The recipient ({receiver_id}) forwarded funds within minutes "
                f"of receiving them. This is an indicator worth investigating, "
                f"but is not proof of wrongdoing."
            ),
            "weight": weight,
        })
        flags.append({"pattern": "RAPID_ONWARD", "accounts": [receiver_id],
                       "explanation": f"Funds were forwarded rapidly after receipt. "
                       "A graph connection is an indicator, NOT proof of wrongdoing."})

    # Multi-hop
    if multi_hop:
        weight = 10
        score += weight
        reasons.append({
            "code": "MULTI_HOP",
            "layer": "graph",
            "text": (
                f"Multi-hop fund flow detected involving {len(multi_hop)} path(s). "
                f"This is an indicator, NOT proof of wrongdoing."
            ),
            "weight": weight,
        })
        all_accounts = set()
        for path in multi_hop:
            all_accounts.update(path)
        flags.append({"pattern": "MULTI_HOP", "accounts": list(all_accounts),
                       "explanation": "Multi-hop fund flow detected. "
                       "A graph connection is an indicator, NOT proof of wrongdoing."})

    score = min(score, 100)
    return LayerResult(score=score, reasons=reasons, flags=flags)
