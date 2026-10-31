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
import os
import re
import time
from typing import Any, Dict, List, Optional

try:
    import httpx
except ImportError:
    httpx = None

from app.config import settings


def _format_amount(amount: Any) -> str:
    """Format numeric amount into Indian Rupee string."""
    try:
        val = float(amount)
        return f"₹{val:,.2f}"
    except (ValueError, TypeError):
        return f"₹{amount}"


def _generate_deterministic_explanation(
    transaction_data: Dict[str, Any],
    risk_assessment: Dict[str, Any],
    language: str = "en",
) -> Dict[str, Any]:
    """Generates a rule-grounded, context-aware explanation and safety tips.

    This deterministic generator guarantees 100% adherence to detected triggers,
    eliminates hallucinations, and serves as an instant fallback during network
    isolation or when external API keys are unavailable.
    """
    score = int(risk_assessment.get("score", 0))
    category = str(risk_assessment.get("category", "LOW")).upper()
    reasons = risk_assessment.get("reasons", [])
    if isinstance(reasons, list) and reasons and isinstance(reasons[0], dict):
        reason_texts = [r.get("text", "") for r in reasons if r.get("text")]
    elif isinstance(reasons, list):
        reason_texts = [str(r) for r in reasons]
    else:
        reason_texts = []

    txn_type = str(transaction_data.get("transaction_type") or transaction_data.get("type") or "P2P").upper()
    amount_str = _format_amount(transaction_data.get("amount", 0))
    sender_upi = str(transaction_data.get("sender_upi") or transaction_data.get("sender_id") or "Sender")
    receiver_upi = str(transaction_data.get("receiver_upi") or transaction_data.get("receiver_id") or "Beneficiary")

    is_hindi = (language.lower().strip() == "hi")

    # Detect specific risk facets
    is_collect = (txn_type == "COLLECT_REQUEST") or any("collect" in r.lower() for r in reason_texts)
    is_impersonation = any(k in receiver_upi.lower() for k in ["kyc", "refund", "support", "desk", "verify"]) or any("impersonat" in r.lower() or "mimic" in r.lower() for r in reason_texts)
    is_brand_spoof = any("brand spoof" in r.lower() or "typosquat" in r.lower() for r in reason_texts)
    is_mule = any("mule" in r.lower() or "rapid onward" in r.lower() or "crypto" in receiver_upi.lower() for r in reason_texts)
    is_nocturnal = any("nocturnal" in r.lower() or "unusual hour" in r.lower() for r in reason_texts)
    is_blacklist = any("registry" in r.lower() or "blacklist" in r.lower() or "threat intelligence" in r.lower() for r in reason_texts)

    if category == "HIGH":
        if is_hindi:
            summary = "उच्च जोखिम संकेत: भुगतान विवरण की जांच आवश्यक"
            if is_collect:
                exp = (
                    f"यह {amount_str} की भुगतान अनुरोध है; इसे मंजूर करने पर आपके खाते से राशि कट सकती है। "
                    "पैसे प्राप्त करने के लिए UPI PIN की जरूरत नहीं होती। PayShield केवल जोखिम का आकलन करता है "
                    "और भुगतान को रोकता नहीं है।"
                )
            elif is_impersonation or is_brand_spoof:
                exp = (
                    f"लाभार्थी आईडी ({receiver_upi}) में बैंक, रिफंड या सत्यापन से जुड़े शब्द हैं। "
                    "यह संकेत अपने-आप धोखाधड़ी की पुष्टि नहीं करता; भुगतान से पहले आधिकारिक संपर्क माध्यम से जांचें।"
                )
            elif is_mule or is_blacklist:
                exp = (
                    f"लाभार्थी आईडी ({receiver_upi}) से जुड़े स्थानीय संकेतों ने जोखिम बढ़ाया है। "
                    "ये संकेत सत्यापित शिकायत या अपराध का प्रमाण नहीं हैं।"
                )
            else:
                exp = (
                    f"उच्च जोखिम स्कोर ({score}/100) मिला। आगे बढ़ने से पहले लेन-देन के विवरण की स्वतंत्र रूप से जांच करें; "
                    "PayShield ने भुगतान को रोका नहीं है।"
                )
            tips = [
                "पैसे प्राप्त करने के लिए कभी भी अपना गुप्त UPI पिन दर्ज न करें।",
                "यदि आपने भुगतान अनुरोध शुरू नहीं किया है, तो अपने भुगतान ऐप में उसे अस्वीकार करें।",
                "वास्तविक घटना का संदेह हो तो आधिकारिक साइबर अपराध सहायता चैनल से संपर्क करें।",
                "किसी भी अज्ञात कॉलर या अनधिकृत ऐप के साथ स्क्रीन साझा न करें।",
            ]
        else:
            summary = "High Risk Signals: Verify the payment independently"
            if is_collect:
                exp = (
                    f"This is a payment request for {amount_str}; approving it may debit your account. "
                    "A UPI PIN is not needed to receive money. PayShield only assesses risk and does not stop payments."
                )
            elif is_impersonation or is_brand_spoof:
                exp = (
                    f"The beneficiary handle '{receiver_upi}' contains banking, refund, or verification terms. "
                    "This signal is not proof of fraud; verify using an independently obtained official contact."
                )
            elif is_mule or is_blacklist:
                exp = (
                    f"Local risk indicators matched patterns associated with beneficiary '{receiver_upi}'. "
                    "These indicators are not independently verified reports or proof of wrongdoing."
                )
            else:
                exp = (
                    f"A high heuristic risk score ({score}/100) was calculated. Review the details independently before proceeding; "
                    "PayShield has not blocked or executed this payment."
                )
            tips = [
                "NEVER enter your secret UPI PIN to receive money, refunds, or lottery prizes.",
                "If you did not initiate a payment request, decline it in your payment app.",
                "If you suspect a real incident, contact your bank or an official cybercrime channel.",
                "Never download screen-sharing tools (AnyDesk, TeamViewer) at the request of an unverified caller.",
            ]

    elif category == "MEDIUM":
        if is_hindi:
            summary = "मध्यम जोखिम: संदिग्ध गतिविधि और अपरिचित लाभार्थी"
            exp = (
                f"सावधानी अपेक्षित ({score}/100): कुछ लेन-देन संकेत आपके सामान्य पैटर्न से अलग हैं। "
                "यह संकेत धोखाधड़ी की पुष्टि नहीं करता; भुगतान से पहले प्राप्तकर्ता और उद्देश्य की जांच करें।"
            )
            tips = [
                "UPI पिन दर्ज करने से पहले प्राप्तकर्ता के नाम और फ़ोन नंबर की पुनः पुष्टि करें।",
                "यदि यह किसी अज्ञात व्यक्ति या ऑनलाइन बाज़ार (OLX, आदि) के कहने पर किया जा रहा है, तो रुकें।",
                "बैंक संदर्भ और प्राप्तकर्ता विवरण की जांच करें।",
            ]
        else:
            summary = "Moderate Risk: Behavioral Anomaly & Unfamiliar Payee"
            exp = (
                f"Caution advised ({score}/100): one or more transaction signals differ from the available history. "
                "This is not confirmation of fraud; verify the recipient and payment purpose."
            )
            tips = [
                "Verify the exact beneficiary name displayed on your UPI application screen before entering PIN.",
                "Ensure this transfer was actively initiated by you and not coached by an unverified caller.",
                "Use an out-of-band communication channel (phone call) to confirm beneficiary account authenticity.",
            ]

    else:
        if is_hindi:
            summary = "कम जोखिम संकेत: भुगतान विवरण फिर भी जांचें"
            exp = (
                f"दिए गए विवरण पर कम जोखिम संकेत मिले ({score}/100)। यह भुगतान की सुरक्षा की गारंटी नहीं है; "
                "भुगतान से पहले प्राप्तकर्ता का नाम और राशि जांचें।"
            )
            tips = [
                "हमेशा अंतिम पुष्टि स्क्रीन पर लाभार्थी का नाम ध्यानपूर्वक पढ़ें।",
                "अपना गुप्त UPI पिन किसी भी व्यक्ति के साथ साझा न करें।",
            ]
        else:
            summary = "Low Risk Signals: Verify Before Paying"
            exp = (
                f"Low heuristic risk signals were observed ({score}/100). This does not guarantee that the payment is safe; "
                "verify the recipient and amount before authorizing it."
            )
            tips = [
                "Standard FinTech Precaution: Always verify the beneficiary name on screen before PIN authorization.",
                "Never reveal your UPI PIN or banking passwords to any third party.",
            ]

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

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
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
    except Exception:
        # Fallback will take over gracefully on any network error, timeout, or parsing issue
        return None

    return None


def generate_explanation(
    transaction_data: Dict[str, Any],
    risk_assessment: Dict[str, Any],
    language: str = "en",
) -> Dict[str, Any]:
    """Generates an evidence-grounded natural-language explanation and safety recommendations.

    Attempts live Gemini LLM inference if an API key is configured; otherwise
    seamlessly delivers the rule-grounded deterministic explainer.

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
        amount = transaction_data.get("amount", 0)
        txn_type = transaction_data.get("transaction_type") or transaction_data.get("type", "P2P")
        allowed_types = {"P2P", "P2M", "QR_SCAN", "BBPS", "COLLECT_REQUEST", "PAY"}
        txn_type = txn_type if txn_type in allowed_types else "OTHER"
        reason_codes = []
        for reason in reasons if isinstance(reasons, list) else []:
            code = reason.get("code") if isinstance(reason, dict) else None
            if isinstance(code, str) and re.fullmatch(r"[A-Za-z0-9_]{1,48}", code):
                reason_codes.append(code.upper())

        prompt = f"""You are the PayShield AI FinTech Security Assistant.
Explain this local prototype risk assessment using only the supplied non-identifying fields.
RISK EVALUATION (authoritative; do not contradict):
- Risk score: {score}/100
- Risk category: {category}
- Request type: {txn_type}
- Trigger codes: {json.dumps(reason_codes[:20])}
- Language: {language}

STRICT CONSTRAINTS:
1. Do not claim a bank, NPCI, merchant, threat registry, or payment-provider connection.
2. Do not say that a payment was blocked, intercepted, verified, or executed.
3. Do not claim a person or account committed fraud; risk signals are not proof.
4. Never ask for a PIN, OTP, password, or other secret.
5. If this is a COLLECT_REQUEST, explain that approving may debit money and a PIN is not needed to receive funds.
6. Provide response as a JSON object with:
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
    return det_result
