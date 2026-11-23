import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.audit import record, snapshot
from app.deps import DB, require_roles
from app.models import Role, User
from app.schemas import UserCreate, UserOut, UserUpdate
from app.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])

Owner = Annotated[User, Depends(require_roles())]  # owner only: no other role listed


@router.get("", response_model=list[UserOut])
def list_users(db: DB, _: Owner) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at)))


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(db: DB, actor: Owner, body: UserCreate) -> User:
    email = body.email.lower().strip()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "A user with that email already exists")
    user = User(
        name=body.name,
        email=email,
        password_hash=hash_password(body.password),
        role=body.role,
        created_by_id=actor.id,
    )
    db.add(user)
    db.flush()
    record(db, user_id=actor.id, action="create", obj=user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(db: DB, actor: Owner, user_id: uuid.UUID, body: UserUpdate) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    before = snapshot(user)

    if body.active is False and user.id == actor.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot deactivate yourself")
    if body.role is not None and body.role != Role.owner and user.id == actor.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot remove your own owner role")

    if body.name is not None:
        user.name = body.name
    if body.role is not None:
        user.role = body.role
    if body.active is not None:
        user.active = body.active
    if body.password is not None:
        user.password_hash = hash_password(body.password)

    db.flush()
    record(db, user_id=actor.id, action="update", obj=user, before=before)
    db.commit()
    db.refresh(user)
    return user
