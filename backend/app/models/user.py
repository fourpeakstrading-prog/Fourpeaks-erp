import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import TimestampMixin


class Role(enum.StrEnum):
    """The six roles from spec section 3. A person has exactly one."""

    owner = "owner"
    accountant = "accountant"
    sales = "sales"
    stores = "stores"
    hr = "hr"
    viewer = "viewer"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role, name="role"), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
