"""Tests for /api/urls/scan."""

from __future__ import annotations


def test_url_scan_malformed_invalid(client):
    """Malformed URL must return verdict INVALID, not crash."""
    r = client.post("/api/urls/scan", json={"url": "not a url at all !!!"})
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] == "INVALID"


def test_url_scan_empty_string_invalid(client):
    r = client.post("/api/urls/scan", json={"url": "   "})
    assert r.status_code == 200
    assert r.json()["verdict"] == "INVALID"


def test_url_scan_lookalike_suspicious_or_malicious(client):
    r = client.post("/api/urls/scan", json={"url": "http://paytm-secure.xyz/kyc-update"})
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] in ("SUSPICIOUS", "MALICIOUS")
    assert body["risk_score"] > 0


def test_url_scan_phonepe_lookalike(client):
    r = client.post("/api/urls/scan", json={"url": "http://phonepe-kyc-update.in/verify"})
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] in ("SUSPICIOUS", "MALICIOUS")


def test_url_scan_gpay_refund_lookalike(client):
    r = client.post("/api/urls/scan", json={"url": "http://gpay-refund.top/claim"})
    assert r.status_code == 200
    assert r.json()["verdict"] in ("SUSPICIOUS", "MALICIOUS")


def test_paypal_lookalike_host_is_not_safe(client):
    response = client.post(
        "/api/urls/scan",
        json={"url": "https://login-paypal.com.evil.example/secure"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "SUSPICIOUS"
    assert body["risk_score"] > 0
    assert any(item["code"] == "LOOKALIKE_DOMAIN" for item in body["indicators"])


def test_official_paypal_subdomain_is_not_flagged_as_lookalike(client):
    response = client.post(
        "/api/urls/scan",
        json={"url": "https://secure.paypal.com/account"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "SAFE"
    assert not any(item["code"] == "LOOKALIKE_DOMAIN" for item in body["indicators"])


def test_https_does_not_give_safe(client):
    """HTTPS alone on a suspicious domain must NOT yield SAFE."""
    r = client.post("/api/urls/scan", json={"url": "https://paytm-secure.xyz/login"})
    assert r.status_code == 200
    body = r.json()
    # Should still be SUSPICIOUS or MALICIOUS (not SAFE) despite HTTPS
    assert body["verdict"] != "SAFE"


def test_url_scan_ip_address_suspicious(client):
    r = client.post("/api/urls/scan", json={"url": "http://192.168.1.1/upi-pay"})
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] in ("SUSPICIOUS", "MALICIOUS")


def test_url_scan_has_simulated_true(client):
    r = client.post("/api/urls/scan", json={"url": "http://example.com"})
    assert r.status_code == 200
    assert r.json()["simulated"] is True


def test_url_scan_has_disclaimer(client):
    r = client.post("/api/urls/scan", json={"url": "http://example.com"})
    assert r.status_code == 200
    assert "disclaimer" in r.json()


def test_url_scan_response_shape(client):
    r = client.post("/api/urls/scan", json={"url": "http://example.com"})
    body = r.json()
    for key in ("url", "normalized_url", "verdict", "risk_score", "indicators", "advice"):
        assert key in body
