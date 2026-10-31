"""URL scanning service – rule-based URL analysis.

NEVER makes network calls or visits URLs. All analysis is static/heuristic.
HTTPS alone does NOT make a URL safe.
"""

from __future__ import annotations

import re
from typing import List, Optional
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models import FraudIntelligence


SUSPICIOUS_TLDS = {
    ".xyz", ".top", ".club", ".work", ".buzz", ".gq", ".ml", ".cf",
    ".tk", ".ga", ".click", ".link", ".online", ".site",
    ".icu", ".win", ".bid", ".loan", ".racing",
}

SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "buff.ly",
    "ow.ly", "rebrand.ly", "cutt.ly", "short.io",
}

LOOKALIKE_PATTERNS = [
    r"paytm[^.]*\.", r"phonepe[^.]*\.", r"gpay[^.]*\.",
    r"googlepay[^.]*\.", r"bhim[^.]*\.", r"paypal[^.]*\.", r"upi[^.]*\.",
    r"sbi[^.]*yono", r"icici[^.]*\.", r"hdfc[^.]*\.",
]

LEGIT_DOMAINS = {
    "paytm.com", "phonepe.com", "pay.google.com", "google.com",
    "sbi.co.in", "icicibank.com", "hdfcbank.com", "paypal.com",
}

SUSPICIOUS_KEYWORDS = [
    "kyc", "refund", "reward", "verify", "update", "lottery",
    "cashback", "prize", "winner", "claim", "urgent", "blocked",
    "suspended", "reactivate",
]


def scan_url(url: str, db: Optional[Session] = None) -> dict:
    """Scan a URL for fraud indicators (no network calls, static analysis only).

    Args:
        url: The URL string to analyse.
        db: Optional database session for intelligence lookups.

    Returns:
        dict with keys: url, normalized_url, verdict, risk_score, indicators, advice
    """
    indicators: List[dict] = []
    score = 0
    raw_url = url.strip()
    normalized = raw_url

    # Try to parse
    try:
        if not raw_url or " " in raw_url:
            raise ValueError("empty or contains spaces")
        if not raw_url.startswith(("http://", "https://")):
            normalized = "http://" + raw_url
        parsed = urlparse(normalized)
        if not parsed.hostname:
            raise ValueError("no hostname")
        if not re.match(r"^[a-zA-Z0-9.-]+$", parsed.hostname):
            raise ValueError("invalid characters in hostname")
        if "." not in parsed.hostname and parsed.hostname != "localhost":
            raise ValueError("hostname missing domain")
    except Exception:
        return {
            "url": raw_url,
            "normalized_url": normalized,
            "verdict": "INVALID",
            "risk_score": 0,
            "indicators": [{"code": "INVALID_URL", "text": "The URL could not be parsed or has no hostname."}],
            "advice": "This URL appears malformed or invalid.",
        }

    hostname = (parsed.hostname or "").lower()
    path = (parsed.path or "").lower()
    full_lower = normalized.lower()

    # '@' in URL
    if "@" in parsed.netloc:
        score += 30
        indicators.append({
            "code": "AT_SIGN_IN_URL",
            "text": "URL contains '@' which can disguise the real destination.",
        })

    # IP address host
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", hostname):
        score += 25
        indicators.append({
            "code": "IP_ADDRESS_HOST",
            "text": "URL uses a raw IP address instead of a domain name.",
        })

    # Punycode
    if any(part.startswith("xn--") for part in hostname.split(".")):
        score += 20
        indicators.append({
            "code": "PUNYCODE_DOMAIN",
            "text": "Domain uses Punycode encoding, which can be used for visual spoofing.",
        })

    # Excessive subdomains (>4 parts)
    parts = hostname.split(".")
    if len(parts) > 4:
        score += 15
        indicators.append({
            "code": "EXCESSIVE_SUBDOMAINS",
            "text": f"Domain has {len(parts)} levels, unusually deep for a legitimate service.",
        })

    # Suspicious TLD
    for tld in SUSPICIOUS_TLDS:
        if hostname.endswith(tld):
            score += 15
            indicators.append({
                "code": "SUSPICIOUS_TLD",
                "text": f"Domain uses TLD '{tld}' commonly seen in phishing sites.",
            })
            break

    # URL shortener
    if hostname in SHORTENERS:
        score += 15
        indicators.append({
            "code": "URL_SHORTENER",
            "text": "URL shortener detected – real destination is hidden.",
        })

    # Lookalike domains
    is_official_domain = any(
        hostname == domain or hostname.endswith(f".{domain}")
        for domain in LEGIT_DOMAINS
    )
    if not is_official_domain:
        for pattern in LOOKALIKE_PATTERNS:
            if re.search(pattern, hostname, re.IGNORECASE):
                score += 25
                indicators.append({
                    "code": "LOOKALIKE_DOMAIN",
                    "text": f"Domain '{hostname}' resembles a known payment brand but is NOT the official domain.",
                })
                break

    # Suspicious keywords
    found_kw = [kw for kw in SUSPICIOUS_KEYWORDS if kw in path or kw in hostname]
    if found_kw:
        add = min(len(found_kw) * 5, 20)
        score += add
        indicators.append({
            "code": "SUSPICIOUS_KEYWORDS",
            "text": f"URL contains suspicious keywords: {', '.join(found_kw)}.",
        })

    # Fraud intelligence lookup (ignore RETRACTED)
    if db is not None:
        intel_rows = (
            db.query(FraudIntelligence)
            .filter(
                FraudIntelligence.indicator_type.in_(["URL", "DOMAIN"]),
                FraudIntelligence.review_status != "RETRACTED",
            )
            .all()
        )
        for ind in intel_rows:
            iv = ind.indicator_value.lower()
            if ind.indicator_type == "URL" and iv in full_lower:
                w = int(ind.confidence * 30)
                score += w
                indicators.append({
                    "code": "INTEL_URL_MATCH",
                    "text": f"URL matches a known fraud indicator (confidence: {ind.confidence:.0%}, status: {ind.review_status}).",
                })
            elif ind.indicator_type == "DOMAIN" and iv in hostname:
                w = int(ind.confidence * 25)
                score += w
                indicators.append({
                    "code": "INTEL_DOMAIN_MATCH",
                    "text": f"Domain matches a known fraud indicator (confidence: {ind.confidence:.0%}, status: {ind.review_status}).",
                })

    # HTTPS note – HTTPS does NOT make a URL safe
    if parsed.scheme == "https":
        indicators.append({
            "code": "HTTPS_NOTE",
            "text": "HTTPS encrypts data but does NOT verify legitimacy. Phishing sites also use HTTPS.",
        })

    score = min(score, 100)

    # Verdict
    non_note = [i for i in indicators if i["code"] != "HTTPS_NOTE"]
    if score >= 70:
        verdict = "MALICIOUS"
    elif score >= 30 or non_note:
        verdict = "SUSPICIOUS"
    else:
        verdict = "SAFE"

    if verdict == "MALICIOUS":
        advice = (
            "Strong indicators of a malicious URL. Do NOT click, enter credentials, "
            "or download anything from this link. HTTPS does not make a site safe."
        )
    elif verdict == "SUSPICIOUS":
        advice = (
            "This URL has suspicious characteristics. Do not enter personal information "
            "or financial details. HTTPS alone does not make a site safe."
        )
    else:
        advice = (
            "No strong indicators detected, but always be cautious. "
            "Never enter PINs, OTPs, or passwords via unsolicited links. "
            "HTTPS does not guarantee safety."
        )

    return {
        "url": raw_url,
        "normalized_url": normalized,
        "verdict": verdict,
        "risk_score": score,
        "indicators": indicators,
        "advice": advice,
    }
