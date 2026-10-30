"""Playbook matching – pattern-based fraud scenario detection.

Each playbook defines a known fraud pattern with a human-readable warning
and recommended action. The ML teammate can add ML-based playbooks later.

Default playbooks (rule-based):
- FAKE_COLLECT_REQUEST
- REFUND_SCAM (refund_message -> link_click -> collect_request)
- LOTTERY_PRIZE
- FAKE_KYC
- REMOTE_ACCESS_APP
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class PlaybookMatch:
    """A matched fraud playbook."""
    playbook_id: str
    name: str
    warning: str
    recommended_action: str
    score_contribution: int  # how much this adds to total score


# Playbook definitions
PLAYBOOKS = {
    "FAKE_COLLECT_REQUEST": {
        "playbook_id": "PB_FAKE_COLLECT",
        "name": "FAKE_COLLECT_REQUEST",
        "warning": (
            "This appears to be a fake collect request designed to trick you "
            "into sending money. Legitimate refunds are credited automatically "
            "and never require you to approve a collect request."
        ),
        "recommended_action": "STOP_AND_REVIEW",
        "score_contribution": 25,
    },
    "REFUND_SCAM": {
        "playbook_id": "PB_REFUND_SCAM",
        "name": "REFUND_SCAM",
        "warning": (
            "This matches the pattern of a refund scam: an unsolicited refund "
            "message followed by a link and a collect request. Do NOT approve."
        ),
        "recommended_action": "STOP_AND_REVIEW",
        "score_contribution": 30,
    },
    "LOTTERY_PRIZE": {
        "playbook_id": "PB_LOTTERY",
        "name": "LOTTERY_PRIZE",
        "warning": (
            "This message mentions a lottery or prize. Legitimate lotteries "
            "never require you to send money to claim winnings."
        ),
        "recommended_action": "STOP_AND_REVIEW",
        "score_contribution": 25,
    },
    "FAKE_KYC": {
        "playbook_id": "PB_FAKE_KYC",
        "name": "FAKE_KYC",
        "warning": (
            "This appears to be a fake KYC update request. Your bank will "
            "never ask you to update KYC through UPI collect requests or "
            "unsolicited links."
        ),
        "recommended_action": "STOP_AND_REVIEW",
        "score_contribution": 25,
    },
    "REMOTE_ACCESS_APP": {
        "playbook_id": "PB_REMOTE_ACCESS",
        "name": "REMOTE_ACCESS_APP",
        "warning": (
            "References to remote access applications detected. Never install "
            "screen-sharing or remote access apps at a caller's request."
        ),
        "recommended_action": "STOP_AND_REVIEW",
        "score_contribution": 20,
    },
}


def match_playbooks(ctx: Dict[str, Any]) -> List[PlaybookMatch]:
    """Match transaction context against known fraud playbooks.

    Args:
        ctx: RiskContext dict containing:
            - request_type: str
            - message_text: optional str
            - events: optional list[str]
            - url: optional str
            - unsolicited: bool
            - intel_hits: list of intelligence matches

    Returns:
        List of matched PlaybookMatch objects.
    """
    matches: List[PlaybookMatch] = []
    request_type = ctx.get("request_type", "PAY")
    message = (ctx.get("message_text") or "").lower()
    events = [e.lower() for e in (ctx.get("events") or [])]
    url = (ctx.get("url") or "").lower()
    unsolicited = ctx.get("unsolicited", False)

    # FAKE_COLLECT_REQUEST: collect request + (unsolicited OR suspicious message)
    if request_type == "COLLECT_REQUEST":
        refund_keywords = ["refund", "cashback", "reward", "prize", "approved", "receive"]
        if unsolicited or any(kw in message for kw in refund_keywords):
            pb = PLAYBOOKS["FAKE_COLLECT_REQUEST"]
            matches.append(PlaybookMatch(**pb))

    # REFUND_SCAM: refund_message event + link_click event + collect_request event
    if ("refund_message" in events and "link_click" in events and
            "collect_request" in events):
        pb = PLAYBOOKS["REFUND_SCAM"]
        matches.append(PlaybookMatch(**pb))

    # LOTTERY_PRIZE: message contains lottery/prize/winner keywords
    lottery_keywords = ["lottery", "prize", "winner", "jackpot", "congratulations",
                        "you have won", "claim your"]
    if any(kw in message for kw in lottery_keywords):
        pb = PLAYBOOKS["LOTTERY_PRIZE"]
        matches.append(PlaybookMatch(**pb))

    # FAKE_KYC: message/URL contains KYC keywords
    kyc_keywords = ["kyc", "kyc update", "kyc verification", "verify your account",
                    "account blocked", "account suspended"]
    if any(kw in message for kw in kyc_keywords) or "kyc" in url:
        pb = PLAYBOOKS["FAKE_KYC"]
        matches.append(PlaybookMatch(**pb))

    # REMOTE_ACCESS_APP: message mentions remote access tools
    remote_keywords = ["anydesk", "teamviewer", "quicksupport", "remote access",
                       "screen share", "screen sharing"]
    if any(kw in message for kw in remote_keywords):
        pb = PLAYBOOKS["REMOTE_ACCESS_APP"]
        matches.append(PlaybookMatch(**pb))

    return matches
