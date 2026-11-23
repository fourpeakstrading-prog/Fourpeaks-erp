import enum
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import TimestampMixin

# OMR has three decimal places (baisa). 18 digits is plenty for a small company.
Money = Numeric(18, 3)


class AccountType(enum.StrEnum):
    asset = "asset"
    liability = "liability"
    equity = "equity"
    income = "income"
    expense = "expense"


class Account(TimestampMixin, Base):
    """Chart of accounts (spec 5.1). Codes are four digits and unique."""

    __tablename__ = "accounts"

    code: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[AccountType] = mapped_column(
        Enum(AccountType, name="account_type"), nullable=False
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # System accounts are the ones other modules post to; they cannot be deactivated.
    system_key: Mapped[str | None] = mapped_column(String(40), unique=True, nullable=True)


class EntrySource(enum.StrEnum):
    manual = "manual"
    opening = "opening"
    sales_invoice = "sales_invoice"
    purchase_bill = "purchase_bill"
    payment = "payment"
    payroll = "payroll"
    stock_adjustment = "stock_adjustment"
    reversal = "reversal"


class JournalEntry(TimestampMixin, Base):
    """One balanced set of debits and credits (spec 5.1)."""

    __tablename__ = "journal_entries"

    number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source: Mapped[EntrySource] = mapped_column(
        Enum(EntrySource, name="entry_source"), nullable=False
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    narration: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reverses_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=True
    )
    reversed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=True
    )

    lines: Mapped[list["JournalLine"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan", order_by="JournalLine.position"
    )


class JournalLine(Base):
    __tablename__ = "journal_lines"
    __table_args__ = (
        CheckConstraint("debit >= 0 AND credit >= 0", name="ck_line_non_negative"),
        CheckConstraint(
            "(debit > 0 AND credit = 0) OR (credit > 0 AND debit = 0)",
            name="ck_line_one_side",
        ),
        UniqueConstraint("entry_id", "position", name="uq_line_position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True
    )
    debit: Mapped[Decimal] = mapped_column(Money, default=Decimal("0"), nullable=False)
    credit: Mapped[Decimal] = mapped_column(Money, default=Decimal("0"), nullable=False)
    description: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    # Contact link arrives with stage 3; kept nullable now so the schema is stable.
    contact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    entry: Mapped[JournalEntry] = relationship(back_populates="lines")
    account: Mapped[Account] = relationship()


class AccountingPeriod(TimestampMixin, Base):
    """One row per month. Closing sets closed=True and locks every entry in it."""

    __tablename__ = "accounting_periods"
    __table_args__ = (UniqueConstraint("year", "month", name="uq_period"),)

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
