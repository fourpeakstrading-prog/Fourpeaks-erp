from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Role, User
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

DB = Annotated[Session, Depends(get_db)]


def get_current_user(db: DB, token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    user = db.get(User, user_id)
    if user is None or not user.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or deactivated")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: Role) -> Callable[[User], User]:
    """Dependency factory: the current user must hold one of the given roles.

    The owner role passes every check, matching spec section 3 ("nothing is blocked").
    """

    def checker(user: CurrentUser) -> User:
        if user.role == Role.owner or user.role in roles:
            return user
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot do this")

    return checker
