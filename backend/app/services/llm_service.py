"""PayShield AI – LLM & GenAI Explanation Service.

Provides structured, evidence-grounded natural-language risk explanations and
actionable safety advice for UPI transactions.

Architecture:
1. Strict Grounding: Every explanation is derived directly from the authoritative
   risk score, category, playbook matches, graph patterns, and detected reasons.
   The LLM/explainer never invents transaction facts and never overrides or
   contradicts the risk score.
2. Dual-Engine Capability:
   - Primary: Google Gemini API (gemini-1.5-flash) via lightweight HTTP client
     when GEMINI_API_KEY or LLM_API_KEY is configured.
   - Robust Fallback: Built-in deterministic FinTech Heuristic Explainer that
     produces comprehensive, contextual explanations and safety recommendations
     with zero external dependencies or latency penalty.
3. Multi-Lingual Support: Generates safety warnings in English and Hindi (Devanagari).
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

try:
    import httpx
except ImportError:
    httpx = None

from app.config import settings

logger = logging.getLogger(__name__)


def _generate_deterministic_explanation(
    transaction_data: Dict[str, Any],
    risk_assessment: Dict[str, Any],
    language: str = "en",
) -> Dict[str, Any]:
    """Explain the local risk result without asserting unverified facts."""
    score = int(risk_assessment.get("score", 0))
    category = str(risk_assessment.get("category", "LOW")).upper()
    reasons = risk_assessment.get("reasons", [])
    if isinstance(reasons, list) and reasons and isinstance(reasons[0], dict):
        reason_texts = [str(r.get("text", "")).strip() for r in reasons if r.get("text")]
    elif isinstance(reasons, list):
        reason_texts = [str(r) for r in reasons]
    else:
        reason_texts = []

    is_hindi = (language.lower().strip() == "hi")
    evidence = "; ".join(reason_texts[:3]) or "No additional rule trigger was recorded."
    is_collect = str(
        transaction_data.get("transaction_type") or transaction_data.get("type") or ""
    ).upper() == "COLLECT_REQUEST"
    if category == "HIGH":
        summary = "High local risk score — review recommended"
        exp = (
            f"PayShield assigned a local heuristic risk score of {score}/100. "
            f"Recorded signals: {evidence} This is advisory, not proof of fraud, "
            "a payment-provider decision, or a blocked payment."
        )
        tips = [
            "Pause and independently verify the recipient and reason for the request.",
            "Never share your UPI PIN or OTP; a PIN authorizes a debit.",
            "If you suspect fraud, contact your bank through its official channel.",
        ]
    elif category == "MEDIUM":
        summary = "Medium local risk score — verify before proceeding"
        exp = (
            f"PayShield assigned a local heuristic risk score of {score}/100. "
            f"Recorded signals: {evidence} The score is advisory and does not establish fraud."
        )
        tips = [
            "Verify the recipient using a trusted, independent channel.",
            "Review the amount and transaction details before authorizing.",
            "Never share your UPI PIN or OTP.",
        ]
    else:
        summary = "Low local risk score — not a guarantee of safety"
        exp = (
            f"PayShield assigned a local heuristic risk score of {score}/100. "
            f"Recorded signals: {evidence} A low score is not a guarantee that a transaction is safe."
        )
        tips = [
            "Confirm the recipient and amount in your payment app.",
            "Never share your UPI PIN or OTP.",
        ]

    if is_hindi:
        summary = f"स्थानीय नियम-आधारित जोखिम स्कोर {score}/100"
        exp = (
            f"PayShield ने स्थानीय नियमों के आधार पर {score}/100 जोखिम स्कोर दिया। "
            f"दर्ज संकेत: {evidence} यह सलाह है—धोखाधड़ी का प्रमाण या भुगतान रोकने का निर्णय नहीं।"
        )
        tips = [
            "भुगतान से पहले प्राप्तकर्ता और राशि की स्वतंत्र रूप से पुष्टि करें।",
            "अपना UPI PIN या OTP किसी के साथ साझा न करें।",
            "संदेह होने पर अपने बैंक के आधिकारिक माध्यम से संपर्क करें।",
        ]
        if is_collect:
            tips.insert(0, "पैसे प्राप्त करने के लिए UPI PIN दर्ज न करें।")

    return {
        "explanation": exp,
        "safety_recommendations": tips,
        "risk_level_summary": summary,
        "model_used": "PayShield Heuristic Explainer Engine (Deterministic Grounded)",
        "llm_status": "HEURISTIC_FALLBACK",
        "is_grounded": True,
        "language": "hi" if is_hindi else "en",
    }


def _call_gemini_api(
    prompt: str,
    api_key: str,
    model_name: str = "gemini-1.5-flash",
    timeout: float = 5.0,
) -> Optional[Dict[str, Any]]:
    """Calls Google Gemini API using httpx with strict timeout and JSON extraction."""
    if not httpx or not api_key:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 600,
            "responseMimeType": "application/json",
        },
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        raw_text = parts[0]["text"].strip()
                        return json.loads(raw_text)
            else:
                logger.warning("Gemini explanation request returned HTTP %s", resp.status_code)
    except Exception as exc:
        logger.warning("Gemini explanation request failed (%s)", type(exc).__name__)
        return None

    return None


def generate_explanation(
    transaction_data: Dict[str, Any],
    risk_assessment: Dict[str, Any],
    language: str = "en",
) -> Dict[str, Any]:
    """Generates an evidence-grounded natural-language explanation and safety recommendations.

    Attempts Gemini inference using non-identifying risk metadata if a key is
    configured; otherwise returns a local deterministic explanation.

    Args:
        transaction_data: Dict containing sender, receiver, amount, type, time, etc.
        risk_assessment: Dict containing score, category, reasons, action, etc.
        language: "en" (English) or "hi" (Hindi).

    Returns:
        Structured explanation dict with explanation text, safety tips, summary,
        model identification, and latency metrics.
    """
    start_time = time.perf_counter()

    # Determine configured API key (env or settings)
    api_key = (
        getattr(settings, "GEMINI_API_KEY", None)
        or getattr(settings, "LLM_API_KEY", None)
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("LLM_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )
    model_name = getattr(settings, "LLM_MODEL", "gemini-1.5-flash")
    timeout = getattr(settings, "LLM_TIMEOUT_SECONDS", 5.0)

    # If Gemini API key is available, attempt live generation
    if api_key and httpx:
        score = risk_assessment.get("score", 0)
        category = risk_assessment.get("category", "LOW")
        reasons = risk_assessment.get("reasons", [])
        txn_type = transaction_data.get("transaction_type") or transaction_data.get("type", "P2P")
        reason_codes = []
        if isinstance(reasons, list):
            for reason in reasons:
                if isinstance(reason, dict) and reason.get("code"):
                    code = re.sub(r"[^A-Za-z0-9_-]", "", str(reason["code"]))[:64]
                    if code:
                        reason_codes.append(code)

        prompt = f"""You are the PayShield AI FinTech Security Assistant.
Explain this local prototype risk assessment clearly and objectively.

RISK EVALUATION (AUTHORITATIVE - DO NOT CONTRADICT):
- Risk Score: {score}/100
- Risk Category: {category}
- Transaction type: {txn_type}
- Non-identifying trigger codes: {json.dumps(reason_codes)}
- Language: {language}

STRICT CONSTRAINTS:
1. Use only the score, category, transaction type, and trigger codes provided.
2. Do not claim a payment was blocked, fraud was verified, or any external registry/provider was checked.
3. Do not invent transaction details, identities, or facts.
4. If this is a COLLECT_REQUEST, state that a UPI PIN must not be shared to receive money.
5. Provide response as a JSON object with:
   - "explanation": (string) 2-3 concise sentences explaining the primary risk factors.
   - "safety_recommendations": (array of 3-4 strings) clear, actionable security instructions.
   - "risk_level_summary": (string) 1-sentence title summary of the risk.
"""
        gemini_result = _call_gemini_api(prompt, api_key=api_key, model_name=model_name, timeout=timeout)
        if (
            gemini_result
            and isinstance(gemini_result, dict)
            and "explanation" in gemini_result
            and "safety_recommendations" in gemini_result
        ):
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            return {
                "explanation": str(gemini_result["explanation"]),
                "safety_recommendations": [str(x) for x in gemini_result.get("safety_recommendations", [])],
                "risk_level_summary": str(gemini_result.get("risk_level_summary", f"{category} Risk Assessment")),
                "model_used": f"Google Gemini ({model_name}) via PayShield GenAI Service",
                "llm_status": "ONLINE",
                "is_grounded": True,
                "language": language,
                "latency_ms": elapsed_ms,
            }

    # Deterministic grounded explainer
    det_result = _generate_deterministic_explanation(transaction_data, risk_assessment, language=language)
    elapsed_ms = int((time.perf_counter() - start_time) * 1000)
    det_result["latency_ms"] = elapsed_ms
    det_result["fallback_reason"] = (
        "GEMINI_UNAVAILABLE" if api_key else "NO_GEMINI_CREDENTIALS"
    )
    return det_result
