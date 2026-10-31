# PayShield Frontend API Integration

The application has two explicit modes:

- **LIVE:** requests the local FastAPI backend. A request failure is shown as an error; demo fixtures are never substituted.
- **MOCK:** uses static/in-memory synthetic fixtures for UI demonstrations. The dashboard identifies them as `DEMO DATA`.

The local backend and stored demo records are synthetic. PayShield has no authorized NPCI, bank, or payment-provider connection, does not monitor real UPI traffic, and cannot execute or block real payments. The final risk decision is heuristic. An optional experimental Random Forest returns a separate estimate trained on generated synthetic labels; it is not validated or used as proof of fraud.

## Configuration

Set `VITE_API_BASE_URL=http://127.0.0.1:8000` in the frontend `.env` if the default API base is unsuitable. All frontend requests and the connection banner use this one setting. Start the frontend at `http://localhost:5173` and the backend from `backend/` at `http://127.0.0.1:8000`. FastAPI CORS allows `http://localhost:5173` and `http://127.0.0.1:5173` by default; `CORS_ORIGINS` can override these origins using a JSON array.

## Endpoints used in LIVE mode

### Health and status

`GET /api/v1/health`

Returns local backend/database status, the rule-based detection engine, an explicit synthetic-data label, and `ml_model.status` (`active`, `disabled`, or `unavailable`). The model status is based on the configured local artifacts and backend dependencies. This is not an NPCI connectivity check.

### Dashboard analytics

`GET /api/v1/fraud/analytics?dateRange=7D&txnType=ALL`

The response contains metrics and chart series calculated from stored transaction and assessment records. `totalTransactions`, `safeTransactions`, `suspiciousTransactions`, `stopReviewRecommendations`, and `assessedTransactions` describe PayShield records/decisions. `blockedTransactions` counts only verified non-simulated provider events. `totalFraudPreventedAmount` is `null` because the prototype has no verified events to support that claim. Empty sets return zero counts and empty/zero-valued series.

Responses include `data_label: "DEMO / SYNTHETIC DATA"`, `simulated: true`, `detection_engine: "rule-based heuristics"`, and `payment_provider_integration: false`.

### Transactions and analysis

- `POST /api/v1/fraud/analyze` accepts P2P, P2M, QR_SCAN, BBPS, or COLLECT_REQUEST records with a positive amount up to ₹10,00,000 and optional `language: "en" | "hi"`, then stores its transaction and risk assessment. Invalid amounts or transaction types return HTTP 422. The response includes local safety guidance in the selected language. When available, `data.ml_model` contains the separate synthetic-trained model estimate, threshold, and feature assumptions; it does not change the heuristic score. A high-risk result is an internal review recommendation only; no payment is executed or blocked.
- `POST /api/risk/assess` returns the same supplemental model estimate alongside its multi-layer heuristic assessment and accepts the same English/Hindi language selection.
- `GET /api/v1/transactions` returns persisted records with the latest assessment. Records without an assessment are `UNASSESSED`; nonexistent detail requests return 404.
- `GET /api/v1/transactions/{id}` returns one stored record and its latest assessment.

### Alerts

`GET /api/v1/fraud/alerts` builds alert entries from persisted medium/high assessments. Resolving an alert records the resolution and note in SQLite; it does not report to a bank, NPCI, or law-enforcement system.

### Investigation and auxiliary screens

- `GET /api/catalog` supplies synthetic local account references for the Merchant Verification screen. A catalog match is not merchant identity verification; no merchant registry is connected.
- `GET /api/accounts/{account_id}/network?depth=2` returns stored graph nodes, edges, and heuristic patterns. Graph links are indicators, not proof of wrongdoing.
- `GET /api/intelligence?limit=100`, `POST /api/intelligence/report`, and `PATCH /api/intelligence/{indicator_id}` read and update the local indicator registry. `VERIFIED` is an internal review state, not independent confirmation.
- `GET /api/grievances?limit=100`, `POST /api/grievances`, and `PATCH /api/grievances/{case_id}` manage the local prototype queue with constrained status transitions. This is not an official bank grievance channel.
- `POST /api/grievances/{case_id}/appeals` and `GET /api/grievances/{case_id}/appeals` persist/retrieve local appeals after a case reaches `RESOLVED` or `REJECTED`; appeals are not sent to an external organization.
- `GET /api/risk/assessments?limit=100` supplies stored assessment references to the grievance form.
- `POST /api/urls/scan` applies static URL heuristics and stored indicator lookups. It does not open or fetch the submitted URL; a SAFE result is not a guarantee.

### Unavailable integrations

- `GET /api/v1/collect-requests` returns an empty unavailable response. Live collect-request actions return HTTP 501.
- `POST /api/v1/fraud/screenshot-ocr` returns HTTP 501 for uploaded images. The explicitly selected `scan-sample-1`, `scan-sample-2`, and `scan-sample-3` responses are synthetic demo examples, not analyzed uploads.
- No fraud-prevention monetary amount, model accuracy, calibrated confidence, latency benchmark, live threat-feed, external merchant verification, or external payment-blocking capability is claimed.

### Merchant demo ledger

- `POST /api/merchant/sessions` creates a locally persisted expected-amount session.
- `GET /api/merchant/transactions/{reference}` retrieves the demo ledger transaction.
- `POST /api/payments/simulate-callback` records a simulated callback after session, merchant, amount, and duplicate-reference checks. This is not confirmation from a payment provider.

Deprecated `/api/v1/demo/...` routes are synthetic examples only and mark their responses as demo data. They are not used by LIVE-mode dashboard requests.
