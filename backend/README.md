# PayShield Backend

FastAPI and SQLAlchemy backend for local, heuristic transaction risk assessment. This prototype has no authorized NPCI, bank, or payment-provider integration and does not execute or block real payments. Risk scores are heuristics, not validated ML output or proof of fraud. Seed data and the existing demo database are synthetic.

## Storage and startup

The default SQLite URL is relative to the process working directory. Start the server from `backend/` to use `backend/payshield.db`:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Startup creates tables in a missing/new database but does not restore a snapshot or seed demo records. Existing files are preserved. If an existing SQLite file is corrupt, startup raises an error and asks for an explicit backup restore rather than silently replacing data.

`python -m app.db.reset` is destructive: it drops tables and loads synthetic records from `app/data/seed.json`. Run it only when you intentionally want to replace the current database. Snapshot restore is also an explicit operation: `python -m app.db.snapshot restore`.

## API used by the dashboard

- `GET /health` and `GET /api/v1/health` report the local service, database check, heuristic engine, and synthetic-data status.
- `POST /api/v1/fraud/analyze` assesses and stores a submitted transaction record; it does not initiate a payment.
- `GET /api/v1/transactions` and `GET /api/v1/transactions/{id}` return stored records and assessments. Missing records return 404.
- `GET /api/v1/fraud/analytics` derives counts and charts from stored records. Provider-blocked counts require verified, non-simulated payment events; fraud-prevented amount is `null` until supported by verified records.
- `GET /api/v1/fraud/alerts` derives alerts from stored medium/high assessments. Resolution notes are persisted.
- `GET /api/v1/collect-requests` reports that no live integration is available; collect actions return 501.
- `POST /api/v1/fraud/screenshot-ocr` rejects uploaded-image analysis with 501. A fixed sample is available only through an explicitly labeled demo sample key.

Deprecated `/api/v1/demo/...` routes return synthetic examples and identify their data as demo. The frontend LIVE mode does not silently substitute these examples when the backend fails.

## Development checks

```powershell
python -m pytest -q
```

Swagger: `http://127.0.0.1:8000/docs`; health: `http://127.0.0.1:8000/health`.
