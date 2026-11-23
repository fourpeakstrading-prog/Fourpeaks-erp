import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.audit import record, snapshot
from app.deps import DB, CurrentUser, require_roles
from app.models import Account, AccountingPeriod, EntrySource, JournalEntry, Role, User
from app.schemas_ledger import (
    AccountCreate,
    AccountOut,
    AccountUpdate,
    EntryCreate,
    EntryOut,
    PeriodIn,
    PeriodOut,
    ReverseIn,
    TrialBalanceLine,
    TrialBalanceOut,
)
from app.services import ledger as svc

router = APIRouter(tags=["ledger"])

Accountant = Annotated[User, Depends(require_roles(Role.accountant))]
Owner = Annotated[User, Depends(require_roles())]


def _rule(e: svc.LedgerError) -> HTTPException:
    return HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


# Chart of accounts -------------------------------------------------------------


@router.get("/accounts", response_model=list[AccountOut])
def list_accounts(db: DB, _: CurrentUser, include_inactive: bool = False) -> list[Account]:
    stmt = select(Account).order_by(Account.code)
    if not include_inactive:
        stmt = stmt.where(Account.active.is_(True))
    return list(db.scalars(stmt))


@router.post("/accounts", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def create_account(db: DB, actor: Accountant, body: AccountCreate) -> Account:
    if db.scalar(select(Account).where(Account.code == body.code)):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Account code {body.code} already exists")
    if body.parent_id and not db.get(Account, body.parent_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Parent account not found")
    acct = Account(**body.model_dump(), created_by_id=actor.id)
    db.add(acct)
    db.flush()
    record(db, user_id=actor.id, action="create", obj=acct)
    db.commit()
    db.refresh(acct)
    return acct


@router.patch("/accounts/{account_id}", response_model=AccountOut)
def update_account(
    db: DB, actor: Accountant, account_id: uuid.UUID, body: AccountUpdate
) -> Account:
    acct = db.get(Account, account_id)
    if acct is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found")
    if body.active is False and acct.system_key:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "System accounts cannot be deactivated")
    before = snapshot(acct)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(acct, k, v)
    db.flush()
    record(db, user_id=actor.id, action="update", obj=acct, before=before)
    db.commit()
    db.refresh(acct)
    return acct


# Journal -----------------------------------------------------------------------


@router.get("/journal", response_model=list[EntryOut])
def list_entries(
    db: DB,
    _: Accountant,
    date_from: date | None = None,
    date_to: date | None = None,
    account_id: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[JournalEntry]:
    stmt = (
        select(JournalEntry)
        .options(selectinload(JournalEntry.lines))
        .order_by(JournalEntry.entry_date.desc(), JournalEntry.number.desc())
        .limit(limit)
        .offset(offset)
    )
    if date_from:
        stmt = stmt.where(JournalEntry.entry_date >= date_from)
    if date_to:
        stmt = stmt.where(JournalEntry.entry_date <= date_to)
    if account_id:
        stmt = stmt.where(JournalEntry.lines.any(account_id=account_id))
    return list(db.scalars(stmt))


@router.get("/journal/{entry_id}", response_model=EntryOut)
def get_entry(db: DB, _: Accountant, entry_id: uuid.UUID) -> JournalEntry:
    e = db.get(JournalEntry, entry_id, options=[selectinload(JournalEntry.lines)])
    if e is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entry not found")
    return e


@router.post("/journal", response_model=EntryOut, status_code=status.HTTP_201_CREATED)
def post_manual_entry(db: DB, actor: Accountant, body: EntryCreate) -> JournalEntry:
    try:
        entry = svc.post_entry(
            db,
            entry_date=body.entry_date,
            source=EntrySource.manual,
            lines=[svc.LineInput(**ln.model_dump()) for ln in body.lines],
            narration=body.narration,
            user_id=actor.id,
        )
    except svc.LedgerError as e:
        db.rollback()
        raise _rule(e) from e
    db.commit()
    return db.get(JournalEntry, entry.id, options=[selectinload(JournalEntry.lines)])


@router.post("/journal/{entry_id}/reverse", response_model=EntryOut, status_code=201)
def reverse(db: DB, actor: Accountant, entry_id: uuid.UUID, body: ReverseIn) -> JournalEntry:
    e = db.get(JournalEntry, entry_id, options=[selectinload(JournalEntry.lines)])
    if e is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entry not found")
    try:
        rev = svc.reverse_entry(db, e, on=body.on, user_id=actor.id, narration=body.narration)
    except svc.LedgerError as err:
        db.rollback()
        raise _rule(err) from err
    db.commit()
    return db.get(JournalEntry, rev.id, options=[selectinload(JournalEntry.lines)])


# Periods -----------------------------------------------------------------------


@router.get("/periods", response_model=list[PeriodOut])
def list_periods(db: DB, _: Accountant) -> list[AccountingPeriod]:
    return list(
        db.scalars(select(AccountingPeriod).order_by(AccountingPeriod.year, AccountingPeriod.month))
    )


@router.post("/periods/close", response_model=PeriodOut)
def close_period(db: DB, actor: Accountant, body: PeriodIn) -> AccountingPeriod:
    try:
        p = svc.close_period(db, body.year, body.month, user_id=actor.id)
    except svc.LedgerError as e:
        db.rollback()
        raise _rule(e) from e
    db.commit()
    db.refresh(p)
    return p


@router.post("/periods/reopen", response_model=PeriodOut)
def reopen_period(db: DB, actor: Owner, body: PeriodIn) -> AccountingPeriod:
    try:
        p = svc.reopen_period(db, body.year, body.month, user_id=actor.id)
    except svc.LedgerError as e:
        db.rollback()
        raise _rule(e) from e
    db.commit()
    db.refresh(p)
    return p


# Reports -----------------------------------------------------------------------


@router.get("/reports/trial-balance", response_model=TrialBalanceOut)
def trial_balance(db: DB, _: CurrentUser, as_of: date | None = None) -> TrialBalanceOut:
    rows = svc.trial_balance(db, as_of=as_of)
    return TrialBalanceOut(
        as_of=as_of,
        rows=[TrialBalanceLine(**r.__dict__) for r in rows],
        total_debit=sum((r.debit for r in rows), svc.ZERO),
        total_credit=sum((r.credit for r in rows), svc.ZERO),
    )
