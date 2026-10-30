# PayShield AI Frontend

React/Vite frontend for PayShield's local, rule-based transaction risk assessment prototype. It is not connected to NPCI, a bank, or a payment provider; it does not monitor real UPI traffic or execute/block payments. Risk scores are heuristics, not validated ML output.

## Modes and data

- **LIVE** calls the local FastAPI endpoints. Failed requests show errors and do not fall back to fixtures.
- **MOCK** uses static/in-memory synthetic fixtures for UI demonstrations and labels them `DEMO DATA`.
- Backend records and the existing SQLite demo dataset are synthetic and labeled `DEMO / SYNTHETIC DATA`. Starting with a new DB yields an empty dashboard.
- Uploaded-image OCR and live collect-request controls are unavailable. Fixed screenshot examples are demo responses, not analyzed uploads.

See [`API_DOCUMENTATION.md`](./API_DOCUMENTATION.md) for connected endpoints and unavailable capabilities.

## Run

```powershell
npm install
npm run dev
```

The app runs at `http://localhost:5173`. Configure `VITE_API_BASE_URL=http://127.0.0.1:8000` if needed. Build with `npm run build`.

The root project README documents how to start the backend and warns about destructive database reset commands.
