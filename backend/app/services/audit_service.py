"""Persist minimal audit metadata without secrets or payment credentials."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditEvent


def record_audit_event(
    db: Session,
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    details: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditEvent(
            event_id=f"AUD_{uuid.uuid4().hex.upper()}",
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            details=details or {},
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    )
