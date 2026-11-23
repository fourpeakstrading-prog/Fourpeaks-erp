import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import Role


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    role: Role
    active: bool
    created_at: datetime


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    role: Role | None = None
    active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    at: datetime
    user_id: uuid.UUID | None
    action: str
    table_name: str
    record_id: str | None
    before: dict[str, Any] | None
    after: dict[str, Any] | None


class CompanySettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company_name: str
    address: str
    cr_number: str
    vat_number: str
    vat_enabled: bool
    currency: str
    currency_decimals: int
    financial_year_start_month: int


class CompanySettingsUpdate(BaseModel):
    company_name: str | None = Field(default=None, min_length=1, max_length=200)
    address: str | None = Field(default=None, max_length=500)
    cr_number: str | None = Field(default=None, max_length=50)
    vat_number: str | None = Field(default=None, max_length=50)
    vat_enabled: bool | None = None
    financial_year_start_month: int | None = Field(default=None, ge=1, le=12)
