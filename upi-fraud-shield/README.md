# PayShield AI Frontend

React/Vite frontend for PayShield's local, rule-based transaction risk assessment prototype. It is not connected to NPCI, a bank, or a payment provider; it does not monitor real UPI traffic or execute/block payments. The final risk score is heuristic. When configured, a synthetic-trained experimental model provides a separate, unvalidated estimate that does not change the score.

## Modes and data

- **LIVE** calls the local FastAPI endpoints. Failed requests show errors and do not fall back to fixtures.
- **MOCK** uses static/in-memory synthetic fixtures for UI demonstrations and labels them `DEMO DATA`.
- Backend records and the existing SQLite demo dataset are synthetic and labeled `DEMO / SYNTHETIC DATA`. Starting with a new DB yields an empty dashboard.
- Uploaded-image OCR and live collect-request controls are unavailable. Fixed screenshot examples are demo responses, not analyzed uploads.
- Merchant ledger sessions and callbacks are explicitly simulated local records; they do not represent provider-confirmed payments.

See [`API_DOCUMENTATION.md`](./API_DOCUMENTATION.md) for connected endpoints and unavailable capabilities.

## Screens

The responsive workspace includes Dashboard, Transaction Risk Checker, Collect Request Protection, Fraud Analytics & Model Status, Fraud Network, Merchant Verification, Fraud Intelligence & Grievance Centre, Suspicious URL Scanner, Transaction History, Alerts & Risk Report, and the retained Evidence Scanner. Merchant lookup is limited to the synthetic local account catalog; it is not external merchant verification.

## Run

```powershell
npm install
npm run dev
```

The app runs at `http://localhost:5173`. Configure `VITE_API_BASE_URL=http://127.0.0.1:8000` if needed. Build with `npm run build`.

The root project README documents how to start the backend and warns about destructive database reset commands.
