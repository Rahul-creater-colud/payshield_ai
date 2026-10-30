"""Idempotent seed loader â€“ loads data/seed.json into the database.

Usage: python -m app.db.seed
"""

from __future__ import annotations

import json
import os

from sqlalchemy.orm import Session

from app.database import engine, SessionLocal, Base
from app.config import settings
from app import models  # noqa: F401


_MODEL_MAP = {
    "demo_users": models.DemoUser,
    "accounts_or_vpas": models.AccountOrVPA,
    "transactions": models.Transaction,
    "graph_edges": models.GraphEdge,
    "fraud_intelligence": models.FraudIntelligence,
    "merchant_sessions": models.MerchantSession,
    "payment_events": models.PaymentEvent,
    "risk_assessments": models.RiskAssessment,
    "grievances": models.Grievance,
}

_PK_MAP = {
    "demo_users": "user_id",
    "accounts_or_vpas": "account_id",
    "transactions": "transaction_id",
    "graph_edges": "id",
    "fraud_intelligence": "indicator_id",
    "merchant_sessions": "session_id",
    "payment_events": "event_id",
    "risk_assessments": "assessment_id",
    "grievances": "case_id",
}


def load_seed(db: Session | None = None, seed_path: str | None = None) -> None:
    """Load seed.json into the database. Skips rows that already exist (idempotent)."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    path = seed_path or settings.SEED_PATH
    if not os.path.exists(path):
        print(f"âœ— Seed file not found: {path}")
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Ensure tables exist
        Base.metadata.create_all(bind=engine)

        # Order matters for FK constraints
        load_order = [
            "demo_users",
            "accounts_or_vpas",
            "transactions",
            "graph_edges",
            "fraud_intelligence",
            "merchant_sessions",
            "payment_events",
            "risk_assessments",
            "grievances",
        ]

        for table_key in load_order:
            rows = data.get(table_key, [])
            if not rows:
                continue

            model_cls = _MODEL_MAP[table_key]
            pk_field = _PK_MAP[table_key]
            inserted = 0

            for row in rows:
                pk_val = row.get(pk_field)
                # For graph_edges, id is auto-increment; skip existence check if id not in row
                if pk_val is not None:
                    existing = db.get(model_cls, pk_val)
                    if existing is not None:
                        continue

                obj = model_cls(**row)
                db.add(obj)
                inserted += 1

            db.commit()
            print(f"  {table_key}: {inserted} inserted, {len(rows) - inserted} skipped")

        print("âœ“ Seed data loaded.")
    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    load_seed()

