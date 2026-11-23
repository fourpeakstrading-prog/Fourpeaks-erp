from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.audit import record, snapshot
from app.deps import DB, CurrentUser, require_roles
from app.models import CompanySettings, User
from app.schemas import CompanySettingsOut, CompanySettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])

Owner = Annotated[User, Depends(require_roles())]


def get_or_create_settings(db) -> CompanySettings:
    row = db.scalar(select(CompanySettings).limit(1))
    if row is None:
        row = CompanySettings(company_name="My Company")
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("", response_model=CompanySettingsOut)
def read_settings(db: DB, _: CurrentUser) -> CompanySettings:
    return get_or_create_settings(db)


@router.patch("", response_model=CompanySettingsOut)
def update_settings(db: DB, actor: Owner, body: CompanySettingsUpdate) -> CompanySettings:
    row = get_or_create_settings(db)
    before = snapshot(row)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    db.flush()
    record(db, user_id=actor.id, action="update", obj=row, before=before)
    db.commit()
    db.refresh(row)
    return row
