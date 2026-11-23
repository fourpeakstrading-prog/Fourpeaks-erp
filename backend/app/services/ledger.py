"""The general ledger. Every module that moves money comes through `post_entry`.

Rules enforced here (spec section 7):
  1. Nothing posted is edited. Corrections are reversals, and both are kept.
  3. Balances are derived from lines, never stored.
  4. Every entry balances, and no entry can be dated inside a closed month.
"""

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import record, snapshot
from app.models import (
    Account,
    AccountingPeriod,
    AccountType,
    EntrySource,
    JournalEntry,
    JournalLine,
)

ZERO = Decimal("0")
Q = Decimal("0.001")  # OMR precision


class LedgerError(ValueError):
    """A business-rule violation. Routers turn this into HTTP 400."""


@dataclass(frozen=True)
class LineInput:
    account_id: uuid.UUID
    debit: Decimal = ZERO
    credit: Decimal = ZERO
    description: str = ""
    contact_id: uuid.UUID | None = None


def _q(x: Decimal) -> Decimal:
    return Decimal(x).quantize(Q)


def period_is_closed(db: Session, d: date) -> bool:
    row = db.scalar(
        select(AccountingPeriod).where(
            AccountingPeriod.year == d.year, AccountingPeriod.month == d.month
        )
    )
    return bool(row and row.closed)


def next_entry_number(db: Session) -> int:
    return (db.scalar(select(func.max(JournalEntry.number))) or 0) + 1


def post_entry(
    db: Session,
    *,
    entry_date: date,
    source: EntrySource,
    lines: list[LineInput],
    narration: str = "",
    source_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None,
    reverses_id: uuid.UUID | None = None,
) -> JournalEntry:
    """Validate and post one balanced journal entry. Does not commit."""
    if len(lines) < 2:
        raise LedgerError("An entry needs at least two lines")
    if period_is_closed(db, entry_date):
        raise LedgerError(f"{entry_date:%B %Y} is closed. Post the correction in an open month.")

    total_debit = ZERO
    total_credit = ZERO
    account_ids = {ln.account_id for ln in lines}
    accounts = {a.id: a for a in db.scalars(select(Account).where(Account.id.in_(account_ids)))}

    for ln in lines:
        debit, credit = _q(ln.debit), _q(ln.credit)
        if debit < ZERO or credit < ZERO:
            raise LedgerError("Amounts cannot be negative")
        if (debit > ZERO) == (credit > ZERO):
            raise LedgerError("Each line must have either a debit or a credit, not both or neither")
        acct = accounts.get(ln.account_id)
        if acct is None:
            raise LedgerError("Unknown account on a line")
        if not acct.active:
            raise LedgerError(f"Account {acct.code} {acct.name} is inactive")
        total_debit += debit
        total_credit += credit

    if total_debit != total_credit:
        raise LedgerError(
            f"Entry does not balance: debits {total_debit} and credits {total_credit}"
        )

    entry = JournalEntry(
        number=next_entry_number(db),
        entry_date=entry_date,
        source=source,
        source_id=source_id,
        narration=narration.strip(),
        reverses_id=reverses_id,
        created_by_id=user_id,
    )
    for pos, ln in enumerate(lines, start=1):
        entry.lines.append(
            JournalLine(
                position=pos,
                account_id=ln.account_id,
                debit=_q(ln.debit),
                credit=_q(ln.credit),
                description=ln.description.strip(),
                contact_id=ln.contact_id,
            )
        )
    db.add(entry)
    db.flush()
    record(db, user_id=user_id, action="post", obj=entry)
    return entry


def reverse_entry(
    db: Session, entry: JournalEntry, *, on: date, user_id: uuid.UUID | None, narration: str = ""
) -> JournalEntry:
    """Create the mirror image of an entry. The original is kept and linked."""
    if entry.reversed_by_id is not None:
        raise LedgerError(f"Entry {entry.number} has already been reversed")
    mirror = [
        LineInput(
            account_id=ln.account_id,
            debit=ln.credit,
            credit=ln.debit,
            description=ln.description,
            contact_id=ln.contact_id,
        )
        for ln in entry.lines
    ]
    rev = post_entry(
        db,
        entry_date=on,
        source=EntrySource.reversal,
        lines=mirror,
        narration=narration or f"Reversal of entry {entry.number}",
        source_id=entry.source_id,
        user_id=user_id,
        reverses_id=entry.id,
    )
    before = snapshot(entry)
    entry.reversed_by_id = rev.id
    db.flush()
    record(db, user_id=user_id, action="reverse", obj=entry, before=before)
    return rev


def close_period(
    db: Session, year: int, month: int, *, user_id: uuid.UUID | None
) -> AccountingPeriod:
    period = db.scalar(
        select(AccountingPeriod).where(
            AccountingPeriod.year == year, AccountingPeriod.month == month
        )
    )
    if period is None:
        period = AccountingPeriod(year=year, month=month, created_by_id=user_id)
        db.add(period)
        db.flush()
    if period.closed:
        raise LedgerError(f"{year}-{month:02d} is already closed")

    # Every earlier month must be closed first, so books close in order.
    first = db.scalar(select(func.min(JournalEntry.entry_date)))
    if first is not None:
        y, m = first.year, first.month
        while (y, m) < (year, month):
            if not period_is_closed(db, date(y, m, 1)):
                raise LedgerError(f"Close {y}-{m:02d} before closing {year}-{month:02d}")
            m += 1
            if m == 13:
                y, m = y + 1, 1

    before = snapshot(period)
    period.closed = True
    start = date(year, month, 1)
    end = date(year + (month == 12), (month % 12) + 1, 1)
    for e in db.scalars(
        select(JournalEntry).where(JournalEntry.entry_date >= start, JournalEntry.entry_date < end)
    ):
        e.locked = True
    db.flush()
    record(db, user_id=user_id, action="close_period", obj=period, before=before)
    return period


def reopen_period(
    db: Session, year: int, month: int, *, user_id: uuid.UUID | None
) -> AccountingPeriod:
    period = db.scalar(
        select(AccountingPeriod).where(
            AccountingPeriod.year == year, AccountingPeriod.month == month
        )
    )
    if period is None or not period.closed:
        raise LedgerError(f"{year}-{month:02d} is not closed")
    # Only the latest closed period can be reopened, keeping the sequence intact.
    later = db.scalar(
        select(AccountingPeriod).where(
            AccountingPeriod.closed.is_(True),
            (AccountingPeriod.year * 100 + AccountingPeriod.month) > year * 100 + month,
        )
    )
    if later:
        raise LedgerError("Reopen later months first")
    before = snapshot(period)
    period.closed = False
    start = date(year, month, 1)
    end = date(year + (month == 12), (month % 12) + 1, 1)
    for e in db.scalars(
        select(JournalEntry).where(JournalEntry.entry_date >= start, JournalEntry.entry_date < end)
    ):
        e.locked = False
    db.flush()
    record(db, user_id=user_id, action="reopen_period", obj=period, before=before)
    return period


# Natural balance side per account type: these show as positive when "normal".
DEBIT_NORMAL = {AccountType.asset, AccountType.expense}


@dataclass
class TrialBalanceRow:
    account_id: uuid.UUID
    code: str
    name: str
    type: AccountType
    debit: Decimal
    credit: Decimal


def trial_balance(db: Session, *, as_of: date | None = None) -> list[TrialBalanceRow]:
    """Per-account totals of all posted lines up to `as_of` (inclusive)."""
    # Date filter lives in the join so accounts with no lines still appear at zero.
    line_join = JournalLine.account_id == Account.id
    if as_of is not None:
        dated = select(JournalLine.id).join(JournalEntry).where(JournalEntry.entry_date <= as_of)
        line_join = line_join & JournalLine.id.in_(dated)
    stmt = (
        select(
            Account.id,
            Account.code,
            Account.name,
            Account.type,
            func.coalesce(func.sum(JournalLine.debit), 0),
            func.coalesce(func.sum(JournalLine.credit), 0),
        )
        .select_from(Account)
        .join(JournalLine, line_join, isouter=True)
        .group_by(Account.id, Account.code, Account.name, Account.type)
        .order_by(Account.code)
    )
    rows = []
    for acct_id, code, name, type_, dr, cr in db.execute(stmt):
        dr, cr = _q(Decimal(dr)), _q(Decimal(cr))
        net = dr - cr
        # Show the net on one side only, the conventional trial balance layout.
        if net >= 0:
            rows.append(TrialBalanceRow(acct_id, code, name, type_, net, ZERO))
        else:
            rows.append(TrialBalanceRow(acct_id, code, name, type_, ZERO, -net))
    return rows


def account_balance(db: Session, account_id: uuid.UUID, *, as_of: date | None = None) -> Decimal:
    """Signed balance: positive means debit balance."""
    stmt = (
        select(func.coalesce(func.sum(JournalLine.debit - JournalLine.credit), 0))
        .select_from(JournalLine)
        .join(JournalEntry)
        .where(JournalLine.account_id == account_id)
    )
    if as_of is not None:
        stmt = stmt.where(JournalEntry.entry_date <= as_of)
    return _q(Decimal(db.scalar(stmt) or 0))
