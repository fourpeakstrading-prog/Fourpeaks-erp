from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.deps import DB, require_roles
from app.models import AuditLog, Role, User
from app.schemas import AuditOut

router = APIRouter(prefix="/audit", tags=["audit"])

Reader = Annotated[User, Depends(require_roles(Role.accountant))]


@router.get("", response_model=list[AuditOut])
def list_audit(
    db: DB,
    _: Reader,
    table_name: str | None = None,
    record_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AuditLog]:
    stmt = select(AuditLog).order_by(AuditLog.at.desc()).limit(limit).offset(offset)
    if table_name:
        stmt = stmt.where(AuditLog.table_name == table_name)
    if record_id:
        stmt = stmt.where(AuditLog.record_id == record_id)
    return list(db.scalars(stmt))
