# PayShield AI – Backend Service

Context-aware UPI fraud prevention system – Hackathon MVP with synthetic data and simulated payment transactions.

---

## Tech Stack
* **Language & Framework**: Python 3.10+ / FastAPI / Starlette
* **Persistence & ORM**: SQLAlchemy 2.x with SQLite (`payshield.db`)
* **Network & Graph Analytics**: NetworkX
* **Validation & Settings**: Pydantic v2 & Pydantic-Settings
* **Testing**: Pytest & HTTPX TestClient

---

## Directory Structure
```
backend/
├── app/
│   ├── main.py              # Application factory & router registration
│   ├── config.py            # Environment configuration & risk thresholds
│   ├── errors.py            # Error envelope { "error": { "code", "message", "details" } }
│   ├── database.py          # SQLAlchemy engine, session generator & auto-recovery
│   ├── models.py            # 9 ORM tables
│   ├── schemas.py           # Pydantic v2 request/response schemas
│   ├── db/
│   │   ├── init_db.py       # Database table initialisation
│   │   ├── seed.py          # Seed loader from JSON
│   │   ├── reset.py         # Full database drop, recreate, seed, and snapshot
│   │   └── snapshot.py      # SQLite fallback snapshot save & restore
│   ├── data/
│   │   ├── seed.json        # Synthetic seed data for scenarios A, B, C, D, LOW
│   │   └── fallback/        # Offline fallback database snapshot
│   ├── engine/              # Modular heuristic risk calculation engines
│   │   ├── behaviour.py     # User baseline deviation & velocity checks
│   │   ├── graph_layer.py   # Fan-in, fan-out, rapid onward & multi-hop checks
│   │   ├── playbooks.py     # Pattern-based scam playbooks (fake collect, refund scam)
│   │   └── scoring.py       # Score combination, risk categorization & ML hook
│   ├── routers/             # API Routers
│   │   ├── health.py        # /health and /api/health
│   │   ├── catalog.py       # /api/catalog
│   │   ├── risk.py          # /api/risk/assess and /api/risk/assessments
│   │   ├── urls.py          # /api/urls/scan
│   │   ├── network.py       # /api/accounts/{id}/network
│   │   ├── grievances.py    # /api/grievances
│   │   ├── dashboard.py     # /api/dashboard/summary
│   │   ├── intelligence.py  # /api/intelligence
│   │   └── admin.py         # /api/admin/reset
│   └── services/            # Business logic orchestration
│       ├── risk_service.py
│       ├── url_service.py
│       ├── graph_service.py
│       ├── grievance_service.py
│       ├── dashboard_service.py
│       └── intelligence_service.py
├── tests/                   # Pytest test suite (93 tests covering all endpoints)
├── pytest.ini               # Test configuration
├── smoke_test.py            # Standalone 50-check end-to-end smoke test
├── requirements.txt         # Python dependencies
├── API_CONTRACT.md          # Complete API specification and contract rules
└── .env.example             # Sample environment variables
```

---

## Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialise / Reset Database
```bash
python -m app.db.reset
```
This drops existing tables, creates all 9 tables, loads `app/data/seed.json`, and updates the fallback snapshot in `app/data/fallback/payshield_snapshot.db`.

### 3. Run Tests
```bash
python -m pytest -q
```
All 93 tests in `tests/` will execute and pass.

You can also run the comprehensive smoke test:
```bash
python smoke_test.py
```

### 4. Start Development Server
```bash
uvicorn app.main:app --reload
```
Once started:
* Interactive Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
* Alternative ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
* Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

## Offline Fallback Snapshot
If the database file is removed or corrupted during a live demonstration, the application automatically restores from `app/data/fallback/payshield_snapshot.db` on startup.
You can also manually restore anytime:
```bash
python -m app.db.snapshot restore
```

---

## Contract & Risk Rules
* **Risk Categories**:
  - `LOW`: 0 – 39 (`PROCEED`)
  - `MEDIUM`: 40 – 69 (`CAUTION_VERIFY`)
  - `HIGH`: 70 – 100 (`STOP_AND_REVIEW`)
* **New Recipient Rule**: Sending to a new recipient alone never yields `HIGH`.
* **Zero Credential Exposure**: Any request containing `pin`, `otp`, `password`, `cvv`, or `secret` is rejected (`422`).
* **URL Static Analysis**: Static scanning without outbound network requests. HTTPS alone never marks a domain safe.
* **Audit Trail**: Grievance status transitions require a reviewer note and prevent reopening resolved/rejected cases.

