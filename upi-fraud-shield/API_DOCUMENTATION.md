# PayShield Frontend API Integration

The application has two explicit modes:

- **LIVE:** requests the local FastAPI backend. A request failure is shown as an error; demo fixtures are never substituted.
- **MOCK:** uses static/in-memory synthetic fixtures for UI demonstrations. The dashboard identifies them as `DEMO DATA`.

The local backend and stored demo records are synthetic. PayShield has no authorized NPCI, bank, or payment-provider connection, does not monitor real UPI traffic, and cannot execute or block real payments. Risk assessment is heuristic, not validated ML output.

## Configuration

Set `VITE_API_BASE_URL=http://127.0.0.1:8000` in the frontend `.env` if the default API base is unsuitable. Start the frontend at `http://localhost:5173` and the backend from `backend/` at `http://127.0.0.1:8000`.

## Endpoints used in LIVE mode

### Health and status

`GET /api/v1/health`

Returns local backend/database status, the rule-based detection engine, and an explicit synthetic-data label. This is not an NPCI connectivity check.

### Dashboard analytics

`GET /api/v1/fraud/analytics?dateRange=7D&txnType=ALL`

The response contains metrics and chart series calculated from stored transaction and assessment records. `totalTransactions`, `safeTransactions`, `suspiciousTransactions`, `stopReviewRecommendations`, and `assessedTransactions` describe PayShield records/decisions. `blockedTransactions` counts only verified non-simulated provider events. `totalFraudPreventedAmount` is `null` because the prototype has no verified events to support that claim. Empty sets return zero counts and empty/zero-valued series.

Responses include `data_label: "DEMO / SYNTHETIC DATA"`, `simulated: true`, `detection_engine: "rule-based heuristics"`, and `payment_provider_integration: false`.

### Transactions and analysis

- `POST /api/v1/fraud/analyze` assesses a submitted test record and stores its transaction and risk assessment. A high-risk result is an internal `STOP_RECOMMENDED` decision only; no payment is executed.
- `GET /api/v1/transactions` returns persisted records with the latest assessment. Records without an assessment are `UNASSESSED`; nonexistent detail requests return 404.
- `GET /api/v1/transactions/{id}` returns one stored record and its latest assessment.

### Alerts

`GET /api/v1/fraud/alerts` builds alert entries from persisted medium/high assessments. Resolving an alert records the resolution and note in SQLite; it does not report to a bank, NPCI, or law-enforcement system.

### Unavailable integrations

- `GET /api/v1/collect-requests` returns an empty unavailable response. Live collect-request actions return HTTP 501.
- `POST /api/v1/fraud/screenshot-ocr` returns HTTP 501 for uploaded images. The fixed sample response is synthetic and clearly labeled; it is not OCR of an uploaded file.
- No fraud-prevention monetary amount, model accuracy, model confidence, latency benchmark, live threat-feed, or external payment-blocking capability is claimed.

Deprecated `/api/v1/demo/...` routes are synthetic examples only and mark their responses as demo data. They are not used by LIVE-mode dashboard requests.
