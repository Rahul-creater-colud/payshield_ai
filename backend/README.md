# PayShield Backend

FastAPI and SQLAlchemy backend for local, heuristic transaction risk assessment. This prototype has no authorized NPCI, bank, or payment-provider integration and does not execute or block real payments. The final risk score is heuristic. An optional experimental Random Forest returns a separate estimate trained on generated synthetic labels; it is not validated ML evidence or proof of fraud. Seed data and the existing demo database are synthetic.

## Storage and startup

The default SQLite URL is relative to the process working directory. Start the server from `backend/` to use `backend/payshield.db`:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

The checked-in `.env.example` uses the same local SQLite default and explicitly allows the Vite development origins `http://localhost:5173` and `http://127.0.0.1:5173`. Copy it to `.env` only if you need to override defaults; do not put production credentials in the example file.

Startup creates tables in a missing/new database but does not restore a snapshot or seed demo records. Existing files are preserved. If an existing SQLite file is corrupt, startup raises an error and asks for an explicit backup restore rather than silently replacing data.

The optional model loads the trusted package and threshold from `ml_model/ml_model/artifacts/best_model.joblib` and `best_threshold.joblib` relative to the project root; legacy `.pkl` artifacts are supported as a fallback. Set `ML_MODEL_DIR` to another trusted model project directory or `ML_MODEL_ENABLED=false` to disable it. `GET /health` reports whether model inference is active, disabled, or unavailable. Missing artifacts or model dependencies leave heuristic assessments available and identify the ML estimate as unavailable. The ML estimate is supplemental and does not change the final risk score; failed-attempt history is not stored and is explicitly identified as an assumed zero in each prediction. Model artifacts are trusted local pickle files; do not load user-uploaded artifacts.

`python -m app.db.reset` is destructive: it drops tables and loads synthetic records from `app/data/seed.json`. Run it only when you intentionally want to replace the current database. Snapshot restore is also an explicit operation: `python -m app.db.snapshot restore`.
The destructive `POST /api/admin/reset` endpoint is disabled by default. Keep `ENABLE_ADMIN=false` outside isolated local demonstrations; do not expose an unauthenticated reset endpoint on a shared or public network.

## API used by the dashboard

- `GET /health` and `GET /api/v1/health` report the local service, database check, heuristic engine, synthetic-data status, and experimental-model availability.
- `POST /api/v1/fraud/analyze` assesses and stores a submitted transaction record, returns a separate experimental ML estimate when available, and provides English or Hindi local safety guidance (`language: "en" | "hi"`); it does not initiate a payment.
- `POST /api/risk/assess` runs the multi-layer heuristic assessment and includes the same supplemental model estimate and language-selectable safety explanation.
- `GET /api/v1/transactions` and `GET /api/v1/transactions/{id}` return stored records and assessments. Missing records return 404.
- `GET /api/v1/fraud/analytics` derives counts and charts from stored records. Provider-blocked counts require verified, non-simulated payment events; fraud-prevented amount is `null` until supported by verified records.
- `GET /api/v1/fraud/alerts` derives alerts from stored medium/high assessments. Resolution notes are persisted.
- `GET /api/v1/collect-requests` reports that no live integration is available; collect actions return 501.
- `POST /api/v1/fraud/screenshot-ocr` rejects uploaded-image analysis with 501. A fixed sample is available only through an explicitly labeled demo sample key.
- `POST /api/merchant/sessions`, `GET /api/merchant/transactions/{reference}`, and `POST /api/payments/simulate-callback` implement a persisted, explicitly simulated ledger. The callback validates session, merchant, amount, and duplicate references; its status is not provider confirmation.
- `POST /api/grievances/{case_id}/appeals` and `GET /api/grievances/{case_id}/appeals` persist/retrieve prototype appeals only after a grievance is resolved or rejected. Grievance status transitions and submissions are recorded as minimal local audit metadata.

Deprecated `/api/v1/demo/...` routes return synthetic examples and identify their data as demo. The frontend LIVE mode does not silently substitute these examples when the backend fails.

## Development checks

```powershell
python -m pytest -q
```

The requirements include `httpx` for the optional Gemini client and FastAPI's test client.

Swagger: `http://127.0.0.1:8000/docs`; health: `http://127.0.0.1:8000/health`.
