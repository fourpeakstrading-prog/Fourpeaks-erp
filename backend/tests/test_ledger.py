"""Tests for the ledger rules in spec section 7. These are the ones that matter most."""

from datetime import date
from decimal import Decimal

import pytest

from app.models import Role
from tests.conftest import login, make_user


@pytest.fixture
def acct(client, db):
    make_user(db, "acct@example.com", Role.accountant)
    return login(client, "acct@example.com", "password123")


@pytest.fixture
def accounts(client, acct):
    rows = client.get("/accounts", headers=acct).json()
    return {r["code"]: r["id"] for r in rows}


def entry(client, headers, lines, on="2026-11-05", narration="test", expect=201):
    r = client.post(
        "/journal",
        headers=headers,
        json={
            "entry_date": on,
            "narration": narration,
            "lines": lines,
        },
    )
    assert r.status_code == expect, r.text
    return r.json()


# Chart of accounts -------------------------------------------------------------


def test_chart_is_seeded_with_29_accounts(accounts):
    assert len(accounts) == 29
    assert "1100" in accounts and "2000" in accounts and "4000" in accounts


def test_accountant_can_add_account_but_not_duplicate_code(client, acct):
    r = client.post(
        "/accounts",
        headers=acct,
        json={
            "code": "6250",
            "name": "Office supplies",
            "type": "expense",
        },
    )
    assert r.status_code == 201
    r = client.post(
        "/accounts",
        headers=acct,
        json={
            "code": "6250",
            "name": "Again",
            "type": "expense",
        },
    )
    assert r.status_code == 409


def test_system_account_cannot_be_deactivated(client, acct, accounts):
    r = client.patch(f"/accounts/{accounts['1100']}", headers=acct, json={"active": False})
    assert r.status_code == 400
    r = client.patch(f"/accounts/{accounts['6200']}", headers=acct, json={"active": False})
    assert r.status_code == 200 and r.json()["active"] is False


def test_sales_role_can_see_accounts_but_not_post(client, db, accounts):
    make_user(db, "sales@example.com", Role.sales)
    h = login(client, "sales@example.com", "password123")
    assert client.get("/accounts", headers=h).status_code == 200
    r = client.post(
        "/journal",
        headers=h,
        json={
            "entry_date": "2026-11-05",
            "lines": [
                {"account_id": accounts["1100"], "debit": "10"},
                {"account_id": accounts["3000"], "credit": "10"},
            ],
        },
    )
    assert r.status_code == 403


# Posting rules -----------------------------------------------------------------


def test_balanced_entry_posts_with_sequential_numbers(client, acct, accounts):
    e1 = entry(
        client,
        acct,
        [
            {"account_id": accounts["1100"], "debit": "1000.500"},
            {"account_id": accounts["3000"], "credit": "1000.500"},
        ],
    )
    e2 = entry(
        client,
        acct,
        [
            {"account_id": accounts["6200"], "debit": "250"},
            {"account_id": accounts["1100"], "credit": "250"},
        ],
    )
    assert e1["number"] == 1 and e2["number"] == 2
    assert e1["source"] == "manual" and e1["locked"] is False
    assert Decimal(e1["lines"][0]["debit"]) == Decimal("1000.500")


def test_unbalanced_entry_is_refused(client, acct, accounts):
    r = client.post(
        "/journal",
        headers=acct,
        json={
            "entry_date": "2026-11-05",
            "lines": [
                {"account_id": accounts["1100"], "debit": "100"},
                {"account_id": accounts["3000"], "credit": "99.999"},
            ],
        },
    )
    assert r.status_code == 400
    assert "does not balance" in r.json()["detail"]


def test_single_line_entry_is_refused(client, acct, accounts):
    r = client.post(
        "/journal",
        headers=acct,
        json={
            "entry_date": "2026-11-05",
            "lines": [
                {"account_id": accounts["1100"], "debit": "100"},
            ],
        },
    )
    assert r.status_code == 422  # schema: min two lines


def test_line_with_both_sides_or_neither_is_refused(client, acct, accounts):
    r = client.post(
        "/journal",
        headers=acct,
        json={
            "entry_date": "2026-11-05",
            "lines": [
                {"account_id": accounts["1100"], "debit": "100", "credit": "100"},
                {"account_id": accounts["3000"], "credit": "0"},
            ],
        },
    )
    assert r.status_code == 400


def test_inactive_account_cannot_be_posted_to(client, acct, accounts):
    client.patch(f"/accounts/{accounts['6200']}", headers=acct, json={"active": False})
    r = client.post(
        "/journal",
        headers=acct,
        json={
            "entry_date": "2026-11-05",
            "lines": [
                {"account_id": accounts["6200"], "debit": "10"},
                {"account_id": accounts["1100"], "credit": "10"},
            ],
        },
    )
    assert r.status_code == 400 and "inactive" in r.json()["detail"]


def test_amounts_are_rounded_to_three_decimals(client, acct, accounts):
    e = entry(
        client,
        acct,
        [
            {"account_id": accounts["1100"], "debit": "10.0004"},
            {"account_id": accounts["3000"], "credit": "10.0004"},
        ],
        expect=422,
    )  # pydantic decimal_places=3 rejects a 4th decimal at the door
    assert e


# Reversal ----------------------------------------------------------------------


def test_reversal_mirrors_lines_and_links_both_ways(client, acct, accounts):
    e = entry(
        client,
        acct,
        [
            {"account_id": accounts["6200"], "debit": "300"},
            {"account_id": accounts["1100"], "credit": "300"},
        ],
    )
    r = client.post(f"/journal/{e['id']}/reverse", headers=acct, json={"on": "2026-11-06"})
    assert r.status_code == 201, r.text
    rev = r.json()
    assert rev["source"] == "reversal" and rev["reverses_id"] == e["id"]
    by_acct = {ln["account_id"]: ln for ln in rev["lines"]}
    assert Decimal(by_acct[accounts["6200"]]["credit"]) == Decimal("300")
    assert Decimal(by_acct[accounts["1100"]]["debit"]) == Decimal("300")

    original = client.get(f"/journal/{e['id']}", headers=acct).json()
    assert original["reversed_by_id"] == rev["id"]

    # Second reversal is refused
    r = client.post(f"/journal/{e['id']}/reverse", headers=acct, json={"on": "2026-11-06"})
    assert r.status_code == 400


def test_there_is_no_edit_or_delete_endpoint_for_entries(client, acct, accounts):
    e = entry(
        client,
        acct,
        [
            {"account_id": accounts["1100"], "debit": "5"},
            {"account_id": accounts["3000"], "credit": "5"},
        ],
    )
    assert client.patch(f"/journal/{e['id']}", headers=acct, json={}).status_code == 405
    assert client.delete(f"/journal/{e['id']}", headers=acct).status_code == 405


# Period close ------------------------------------------------------------------


def test_closed_month_refuses_new_entries_and_locks_existing(client, acct, accounts):
    e = entry(
        client,
        acct,
        [
            {"account_id": accounts["1100"], "debit": "100"},
            {"account_id": accounts["3000"], "credit": "100"},
        ],
        on="2026-10-15",
    )
    r = client.post("/periods/close", headers=acct, json={"year": 2026, "month": 10})
    assert r.status_code == 200 and r.json()["closed"] is True

    assert client.get(f"/journal/{e['id']}", headers=acct).json()["locked"] is True

    r = client.post(
        "/journal",
        headers=acct,
        json={
            "entry_date": "2026-10-20",
            "lines": [
                {"account_id": accounts["1100"], "debit": "1"},
                {"account_id": accounts["3000"], "credit": "1"},
            ],
        },
    )
    assert r.status_code == 400 and "closed" in r.json()["detail"]

    # Reversal of a locked entry must land in an open month
    r = client.post(f"/journal/{e['id']}/reverse", headers=acct, json={"on": "2026-10-31"})
    assert r.status_code == 400
    r = client.post(f"/journal/{e['id']}/reverse", headers=acct, json={"on": "2026-11-01"})
    assert r.status_code == 201


def test_months_must_close_in_order(client, acct, accounts):
    entry(
        client,
        acct,
        [
            {"account_id": accounts["1100"], "debit": "1"},
            {"account_id": accounts["3000"], "credit": "1"},
        ],
        on="2026-09-10",
    )
    r = client.post("/periods/close", headers=acct, json={"year": 2026, "month": 10})
    assert r.status_code == 400 and "Close 2026-09" in r.json()["detail"]


def test_only_owner_can_reopen_and_it_unlocks(client, acct, owner_headers, accounts):
    e = entry(
        client,
        acct,
        [
            {"account_id": accounts["1100"], "debit": "1"},
            {"account_id": accounts["3000"], "credit": "1"},
        ],
        on="2026-10-10",
    )
    client.post("/periods/close", headers=acct, json={"year": 2026, "month": 10})

    assert (
        client.post("/periods/reopen", headers=acct, json={"year": 2026, "month": 10}).status_code
        == 403
    )
    r = client.post("/periods/reopen", headers=owner_headers, json={"year": 2026, "month": 10})
    assert r.status_code == 200 and r.json()["closed"] is False
    assert client.get(f"/journal/{e['id']}", headers=acct).json()["locked"] is False

    log = client.get(
        "/audit", headers=owner_headers, params={"table_name": "accounting_periods"}
    ).json()
    assert [row["action"] for row in log[:2]] == ["reopen_period", "close_period"]


# Trial balance -----------------------------------------------------------------


def test_trial_balance_always_balances_and_nets_each_account(client, acct, accounts):
    entry(
        client,
        acct,
        [
            {"account_id": accounts["1100"], "debit": "5000"},
            {"account_id": accounts["3000"], "credit": "5000"},
        ],
        on="2026-11-01",
    )
    entry(
        client,
        acct,
        [
            {"account_id": accounts["6200"], "debit": "800"},
            {"account_id": accounts["1100"], "credit": "800"},
        ],
        on="2026-11-03",
    )
    entry(
        client,
        acct,
        [
            {"account_id": accounts["1200"], "debit": "1200"},
            {"account_id": accounts["4100"], "credit": "1200"},
        ],
        on="2026-11-10",
    )

    tb = client.get("/reports/trial-balance", headers=acct).json()
    assert Decimal(tb["total_debit"]) == Decimal(tb["total_credit"]) == Decimal("6200")
    rows = {r["code"]: r for r in tb["rows"]}
    assert Decimal(rows["1100"]["debit"]) == Decimal("4200")  # 5000 - 800 netted
    assert Decimal(rows["1100"]["credit"]) == Decimal("0")
    assert Decimal(rows["4100"]["credit"]) == Decimal("1200")

    tb_early = client.get(
        "/reports/trial-balance", headers=acct, params={"as_of": "2026-11-05"}
    ).json()
    assert Decimal(tb_early["total_debit"]) == Decimal("5000")
    assert Decimal({r["code"]: r for r in tb_early["rows"]}["1200"]["debit"]) == Decimal("0")


def test_viewer_can_read_trial_balance_but_not_journal(client, db):
    make_user(db, "viewer@example.com", Role.viewer)
    h = login(client, "viewer@example.com", "password123")
    assert client.get("/reports/trial-balance", headers=h).status_code == 200
    assert client.get("/journal", headers=h).status_code == 403


def test_posting_is_audited(client, acct, owner_headers, accounts):
    e = entry(
        client,
        acct,
        [
            {"account_id": accounts["1100"], "debit": "7"},
            {"account_id": accounts["3000"], "credit": "7"},
        ],
    )
    log = client.get(
        "/audit",
        headers=owner_headers,
        params={"table_name": "journal_entries", "record_id": e["id"]},
    ).json()
    assert log and log[0]["action"] == "post"


def test_entry_date_validation(client, acct, accounts):
    r = client.post(
        "/journal",
        headers=acct,
        json={
            "entry_date": "not-a-date",
            "lines": [
                {"account_id": accounts["1100"], "debit": "1"},
                {"account_id": accounts["3000"], "credit": "1"},
            ],
        },
    )
    assert r.status_code == 422
    assert date(2026, 11, 5)  # keep the import honest
