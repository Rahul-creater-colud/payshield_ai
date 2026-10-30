"""Database engine, session, dependency and declarative Base for PayShield AI."""

from __future__ import annotations

import logging
import os
import shutil
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
_connect_args = {}
if settings.DB_URL.startswith("sqlite"):
    _connect_args["check_same_thread"] = False

engine = create_engine(settings.DB_URL, connect_args=_connect_args, echo=False)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# ---------------------------------------------------------------------------
# Declarative Base (SQLAlchemy 2.x style)
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Startup: auto-restore from snapshot if DB is missing / corrupt
# ---------------------------------------------------------------------------
def ensure_db() -> None:
    """Called at app startup. If the SQLite file is missing or corrupt,
    attempt to restore from the fallback snapshot."""
    if not settings.DB_URL.startswith("sqlite"):
        return

    db_path = settings.DB_URL.replace("sqlite:///", "")
    snapshot_path = settings.SNAPSHOT_PATH

    # Check if DB file exists
    if os.path.exists(db_path):
        # Quick integrity check
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return  # DB is fine
        except Exception:
            logger.warning("Database file appears corrupt. Attempting restore from snapshot.")
            os.remove(db_path)

    # Try to restore
    if os.path.exists(snapshot_path):
        logger.warning("Database file missing. Restoring from fallback snapshot: %s", snapshot_path)
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        shutil.copy2(snapshot_path, db_path)
    else:
        logger.info("No database file and no snapshot found. Will create fresh DB on init.")
