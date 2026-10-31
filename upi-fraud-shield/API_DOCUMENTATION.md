# PayShield Frontend API Integration

The application has two explicit modes:

- **LIVE:** requests the local FastAPI backend. A request failure is shown as an error; demo fixtures are never substituted.
- **MOCK:** uses static/in-memory synthetic fixtures for UI demonstrations. The dashboard identifies them as `DEMO DATA`.

The local backend and stored demo records are synthetic. PayShield has no authorized NPCI, bank, or payment-provider connection, does not monitor real UPI traffic, and cannot execute or block real payments. The final risk decision is heuristic. An optional experimental Random Forest returns a separate estimate trained on generated synthetic labels; it is not validated or used as proof of fraud.

## Configuration

Set `VITE_API_BASE_URL=http://127.0.0.1:8000` in the frontend `.env` if the default API base is unsuitable. Start the frontend at `http://localhost:5173` and the backend from `backend/` at `http://127.0.0.1:8000`.

## Endpoints used in LIVE mode

### Health and status

`GET /api/v1/health`

Returns local backend/database status, the rule-based detection engine, an explicit synthetic-data label, and `ml_model.status` (`active`, `disabled`, or `unavailable`). The model status is based on the configured local artifacts and backend dependencies. This is not an NPCI connectivity check.

### Dashboard analytics

`GET /api/v1/fraud/analytics?dateRange=7D&txnType=ALL`

The response contains metrics and chart series calculated from stored transaction and assessment records. `totalTransactions`, `safeTransactions`, `suspiciousTransactions`, `stopReviewRecommendations`, and `assessedTransactions` describe PayShield records/decisions. `blockedTransactions` counts only verified non-simulated provider events. `totalFraudPreventedAmount` is `null` because the prototype has no verified events to support that claim. Empty sets return zero counts and empty/zero-valued series.

Responses include `data_label: "LOCAL PROTOTYPE RECORDS (MAY INCLUDE SYNTHETIC SEED DATA)"`, `simulated: true`, `detection_engine: "rule-based heuristics"`, and `payment_provider_integration: false`. This avoids asserting that user-submitted rows have synthetic provenance.

### Transactions and analysis

- `POST /api/v1/fraud/analyze` assesses a submitted test record and stores its transaction and risk assessment. When available, `data.ml_model` contains the separate synthetic-trained model estimate, threshold, and feature assumptions; it does not change the heuristic score. A high-risk result is an internal `STOP_RECOMMENDED` decision only; no payment is executed.
- `POST /api/risk/assess` returns the same supplemental model estimate alongside its multi-layer heuristic assessment.
- `GET /api/v1/transactions` returns persisted records with the latest assessment. Records without an assessment are `UNASSESSED`; nonexistent detail requests return 404.
- `GET /api/v1/transactions/{id}` returns one stored record and its latest assessment.

### Alerts

`GET /api/v1/fraud/alerts` builds alert entries from persisted medium/high assessments. Resolving an alert records the resolution and note in SQLite; it does not report to a bank, NPCI, or law-enforcement system.

### Investigation and auxiliary screens

- `GET /api/catalog` supplies synthetic local account references for the Merchant Verification screen. A catalog match is not merchant identity verification; no merchant registry is connected.
- `GET /api/accounts/{account_id}/network?depth=2` returns stored graph nodes, edges, and heuristic patterns. Graph links are indicators, not proof of wrongdoing.
- `GET /api/intelligence?limit=100`, `POST /api/intelligence/report`, and `PATCH /api/intelligence/{indicator_id}` read and update the local indicator registry. `VERIFIED` is an internal review state, not independent confirmation.
- `GET /api/grievances?limit=100`, `POST /api/grievances`, and `PATCH /api/grievances/{case_id}` manage the local prototype queue. This is not an official bank grievance channel.
- `GET /api/risk/assessments?limit=100` supplies stored assessment references to the grievance form.
- `POST /api/urls/scan` applies static URL heuristics and stored indicator lookups. It does not open or fetch the submitted URL; a SAFE result is not a guarantee.
- `POST /api/merchant/sessions` creates a persistent local expected-amount ledger session.
- `POST /api/merchant/sessions/{session_id}/callbacks/simulate` records a clearly simulated callback.
- `GET /api/merchant/sessions/{session_id}/ledger` compares stored callback and expected amounts. A match is simulated only and is not confirmation from a payment provider.

### Optional explanations

When Gemini credentials are configured, only the risk score, category, transaction type, and sanitized rule codes are sent to Gemini. Transaction identifiers, amounts, free-text context, URLs, PINs, and OTPs are not included. If Gemini is not configured or fails, the response identifies the local deterministic heuristic fallback.

### Unavailable integrations

- `GET /api/v1/collect-requests` returns an empty unavailable response. Live collect-request actions return HTTP 501.
- `POST /api/v1/fraud/screenshot-ocr` returns HTTP 501 for uploaded images. The fixed sample response is synthetic and clearly labeled; it is not OCR of an uploaded file.
- No fraud-prevention monetary amount, model accuracy, calibrated confidence, latency benchmark, live threat-feed, external merchant verification, or external payment-blocking capability is claimed.

Deprecated `/api/v1/demo/...` routes are synthetic examples only and mark their responses as demo data. They are not used by LIVE-mode dashboard requests.
