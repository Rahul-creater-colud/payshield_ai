"""Database engine, session, dependency and declarative Base for PayShield AI."""

from __future__ import annotations

import logging
import os
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
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
# Startup: validate existing DB; initialize new schema in application lifespan
# ---------------------------------------------------------------------------
def ensure_db() -> None:
    """Validate an existing SQLite file without replacing application data."""
    if not settings.DB_URL.startswith("sqlite"):
        return

    db_path = settings.DB_URL.replace("sqlite:///", "")
    if os.path.exists(db_path):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            logger.exception("Configured SQLite database is unavailable: %s", db_path)
            raise RuntimeError(
                f"Configured SQLite database is unavailable: {db_path}. "
                "Restore a backup explicitly before restarting."
            ) from exc
    else:
        logger.info("No SQLite database found at %s. A new empty database will be created.", db_path)
