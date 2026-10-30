"""Drop all tables, recreate, and seed.

Usage: python -m app.db.reset
"""

from __future__ import annotations

from app.database import engine, Base
from app import models  # noqa: F401
from app.db.seed import load_seed
from app.db.snapshot import save_snapshot


def reset_db() -> None:
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Seeding...")
    load_seed()
    print("Saving snapshot...")
    save_snapshot()
    print("âœ“ Database reset complete.")


if __name__ == "__main__":
    reset_db()

