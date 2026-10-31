from __future__ import annotations

from app.config import settings
from app.services import llm_service


def test_gemini_prompt_excludes_transaction_identifiers_amount_and_reason_text(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "unit-test-key")
    monkeypatch.setattr(settings, "LLM_API_KEY", None)
    captured = {}

    def fake_call(prompt, **kwargs):
        captured["prompt"] = prompt
        return {
            "explanation": "A local risk score was assigned.",
            "safety_recommendations": ["Verify independently."],
            "risk_level_summary": "Review recommended",
        }

    monkeypatch.setattr(llm_service, "_call_gemini_api", fake_call)
    result = llm_service.generate_explanation(
        {
            "sender_upi": "private-sender@example",
            "receiver_upi": "private-receiver@example",
            "amount": 12345.67,
            "transaction_type": "PAY",
        },
        {
            "score": 82,
            "category": "HIGH",
            "reasons": [
                {
                    "code": "amount_outlier",
                    "text": "Private recipient private-receiver@example triggered rule",
                }
            ],
        },
    )

    assert result["llm_status"] == "ONLINE"
    assert "amount_outlier" in captured["prompt"]
    assert "private-sender@example" not in captured["prompt"]
    assert "private-receiver@example" not in captured["prompt"]
    assert "12345.67" not in captured["prompt"]
    assert "Private recipient" not in captured["prompt"]
    assert "confidence_score" not in result


def test_local_explanation_does_not_claim_verified_fraud_or_blocked_payment(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    monkeypatch.setattr(settings, "LLM_API_KEY", None)
    monkeypatch.setattr(llm_service.os, "getenv", lambda *_args: None)
    result = llm_service.generate_explanation(
        {"transaction_type": "COLLECT_REQUEST", "amount": 9999},
        {"score": 90, "category": "HIGH", "reasons": []},
    )

    assert result["llm_status"] == "HEURISTIC_FALLBACK"
    assert result["fallback_reason"] == "NO_GEMINI_CREDENTIALS"
    assert "not proof of fraud" in result["explanation"]
    assert "blocked payment" in result["explanation"]
    assert "confidence_score" not in result
    assert any("PIN" in tip for tip in result["safety_recommendations"])
