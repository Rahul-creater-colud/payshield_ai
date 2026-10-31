from app.config import settings
from app.services import llm_service


def test_external_explanation_prompt_excludes_transaction_identifiers_and_values(
    monkeypatch,
):
    prompt_capture = {}
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "unit-test-key")
    monkeypatch.setattr(settings, "LLM_API_KEY", None)

    def fake_gemini(prompt, **kwargs):
        prompt_capture["prompt"] = prompt
        return {
            "explanation": "Review the local risk signals.",
            "safety_recommendations": [
                "Verify the recipient independently.",
                "Do not share your UPI PIN.",
                "Review the risk signals before proceeding.",
            ],
            "risk_level_summary": "Review recommended",
        }

    monkeypatch.setattr(llm_service, "_call_gemini_api", fake_gemini)
    result = llm_service.generate_explanation(
        transaction_data={
            "sender_upi": "private-sender@example",
            "receiver_upi": "private-recipient@example",
            "amount": 987654.0,
            "transaction_type": "P2P",
            "timestamp": "private-timestamp",
        },
        risk_assessment={
            "score": 88,
            "category": "HIGH",
            "reasons": [{
                "code": "HEURISTIC_SIGNAL",
                "text": "Private recipient private-recipient@example",
            }],
        },
    )

    prompt = prompt_capture["prompt"]
    assert "private-sender@example" not in prompt
    assert "private-recipient@example" not in prompt
    assert "987654" not in prompt
    assert "private-timestamp" not in prompt
    assert "Private recipient" not in prompt
    assert result["llm_status"] == "ONLINE"
    assert "confidence_score" not in result


def test_deterministic_hindi_safety_message_does_not_claim_payment_blocked(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    monkeypatch.setattr(settings, "LLM_API_KEY", None)
    monkeypatch.setattr(llm_service.os, "getenv", lambda _: None)
    result = llm_service.generate_explanation(
        transaction_data={
            "receiver_upi": "shop@example",
            "amount": 250.0,
            "transaction_type": "COLLECT_REQUEST",
        },
        risk_assessment={"score": 95, "category": "HIGH", "reasons": []},
        language="hi",
    )

    assert result["language"] == "hi"
    assert result["safety_recommendations"]
    assert "भुगतान को रोकता नहीं है" in result["explanation"]
    assert "confidence_score" not in result
    assert result["llm_availability"] == "NOT_CONFIGURED"
    assert "not configured" in result["llm_message"].lower()


def test_failed_external_explanation_reports_deterministic_fallback(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "unit-test-key")
    monkeypatch.setattr(settings, "LLM_API_KEY", None)
    monkeypatch.setattr(llm_service.os, "getenv", lambda _: None)
    monkeypatch.setattr(llm_service, "_call_gemini_api", lambda *args, **kwargs: None)

    result = llm_service.generate_explanation(
        transaction_data={"transaction_type": "P2P", "amount": 500},
        risk_assessment={"score": 10, "category": "LOW", "reasons": []},
    )

    assert result["llm_status"] == "HEURISTIC_FALLBACK"
    assert result["llm_availability"] == "REQUEST_FAILED"
    assert "see backend logs" in result["llm_message"]