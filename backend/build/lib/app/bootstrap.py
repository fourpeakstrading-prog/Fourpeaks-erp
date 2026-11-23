"""First-start setup: create the owner account if the users table is empty."""

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Role, User
from app.security import hash_password

log = logging.getLogger(__name__)


def ensure_first_owner(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(User)):
        return
    s = get_settings()
    db.add(
        User(
            name=s.first_owner_name,
            email=s.first_owner_email.lower().strip(),
            password_hash=hash_password(s.first_owner_password),
            role=Role.owner,
        )
    )
    db.commit()
    log.warning(
        "Created first owner account %s. Change its password after logging in.", s.first_owner_email
    )
