import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import AccountType, EntrySource


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    type: AccountType
    parent_id: uuid.UUID | None
    active: bool
    system_key: str | None


class AccountCreate(BaseModel):
    code: str = Field(min_length=1, max_length=10, pattern=r"^\d+$")
    name: str = Field(min_length=1, max_length=120)
    type: AccountType
    parent_id: uuid.UUID | None = None


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    parent_id: uuid.UUID | None = None
    active: bool | None = None


class LineIn(BaseModel):
    account_id: uuid.UUID
    debit: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=3)
    credit: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=3)
    description: str = Field(default="", max_length=300)

    @field_validator("debit", "credit", mode="before")
    @classmethod
    def _coerce(cls, v):
        return Decimal(str(v)) if v not in (None, "") else Decimal("0")


class EntryCreate(BaseModel):
    entry_date: date
    narration: str = Field(default="", max_length=500)
    lines: list[LineIn] = Field(min_length=2)


class LineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    position: int
    account_id: uuid.UUID
    debit: Decimal
    credit: Decimal
    description: str


class EntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    number: int
    entry_date: date
    source: EntrySource
    source_id: uuid.UUID | None
    narration: str
    locked: bool
    reverses_id: uuid.UUID | None
    reversed_by_id: uuid.UUID | None
    created_at: datetime
    lines: list[LineOut]


class ReverseIn(BaseModel):
    on: date
    narration: str = Field(default="", max_length=500)


class PeriodOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    year: int
    month: int
    closed: bool


class PeriodIn(BaseModel):
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)


class TrialBalanceLine(BaseModel):
    account_id: uuid.UUID
    code: str
    name: str
    type: AccountType
    debit: Decimal
    credit: Decimal


class TrialBalanceOut(BaseModel):
    as_of: date | None
    rows: list[TrialBalanceLine]
    total_debit: Decimal
    total_credit: Decimal
