"""Audit log helper. Every create, edit, delete, post and period close calls `record`."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy.orm import Session

from app.db import Base
from app.models import AuditLog

_SKIP = {"password_hash", "updated_at"}


def snapshot(obj: Base | None) -> dict[str, Any] | None:
    """Plain-JSON copy of a model row, without secrets."""
    if obj is None:
        return None
    out: dict[str, Any] = {}
    for col in obj.__table__.columns:
        if col.name in _SKIP:
            continue
        val = getattr(obj, col.name)
        if isinstance(val, uuid.UUID | Decimal):
            val = str(val)
        elif isinstance(val, datetime | date):
            val = val.isoformat()
        elif isinstance(val, Enum):
            val = val.value
        out[col.name] = val
    return out


def record(
    db: Session,
    *,
    user_id: uuid.UUID | None,
    action: str,
    obj: Base,
    before: dict[str, Any] | None = None,
) -> None:
    """Append one audit row. Call after the change is applied, before commit."""
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            table_name=obj.__tablename__,
            record_id=str(getattr(obj, "id", "")),
            before=before,
            after=snapshot(obj),
        )
    )
