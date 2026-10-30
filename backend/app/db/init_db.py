"""Create all tables defined in models.py.

Usage: python -m app.db.init_db
"""

from __future__ import annotations

from app.database import engine, Base
from app import models  # noqa: F401  â€“ import so all tables are registered


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    print("âœ“ All tables created.")


if __name__ == "__main__":
    init_db()

