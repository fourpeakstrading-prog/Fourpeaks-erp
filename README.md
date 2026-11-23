# Fourpeaks ERP

[![CI](https://github.com/fourpeakstrading-prog/Fourpeaks-erp/actions/workflows/ci.yml/badge.svg)](https://github.com/fourpeakstrading-prog/Fourpeaks-erp/actions/workflows/ci.yml)

Open-source ERP for a small trading and contracting company, built from scratch. FastAPI, PostgreSQL, React.

It is being built for a real company in Oman (OMR, three-decimal currency, VAT designed in but switched off until registration, Bank Muscat statement import, PASI payroll and WPS bank files). The code and the demo data are generic, so it works for any small company that sells products and services.

## Status

Stages 1 and 2 of 7 are done. See [docs/build-plan.md](docs/build-plan.md) for the full plan.

| Stage | What | State |
|---|---|---|
| 1 | Shared core: login, users, roles, audit log, company settings | Done |
| 2 | Chart of accounts and journal, with balance and period-close rules | Done |
| 3 | Contacts, items, sales invoices, customer payments | Next |
| 4 | Purchase orders, receiving, bills, stock | |
| 5 | Bank import and reconciliation, financial reports | |
| 6 | Employees, leave, payroll, bank file | |
| 7 | Dashboard, reminders, VAT switch | |

## Screenshots

| Manual journal entry | Journal with a reversal |
|---|---|
| ![New entry](docs/screenshots/new-entry.png) | ![Journal](docs/screenshots/journal.png) |

| Trial balance | Users (owner view) |
|---|---|
| ![Trial balance](docs/screenshots/trial-balance.png) | ![Users](docs/screenshots/users.png) |

## Run it

You need Docker Desktop. Nothing else.

```bash
git clone https://github.com/fourpeakstrading-prog/Fourpeaks-erp.git
cd Fourpeaks-erp
cp .env.example .env        # then edit SECRET_KEY and the FIRST_OWNER_* values
docker compose up --build
```

Then open http://localhost:3000 and sign in with the `FIRST_OWNER_EMAIL` and `FIRST_OWNER_PASSWORD` from your `.env`. The API is at http://localhost:8000 and its interactive docs at http://localhost:8000/docs.

## How it is built

```
backend/    FastAPI + SQLAlchemy 2 + Alembic, Python 3.12
frontend/   React 19 + TypeScript + Vite, served by nginx in Docker
docs/       Design spec, build plan, screenshots
```

Rules that apply everywhere (from the design spec):

1. Nothing posted is ever edited. It is reversed and redone, and both are kept.
2. Number sequences run without gaps.
3. Balances and stock on hand are always derived from lines and movements, never stored and adjusted by hand.
4. Every journal entry must balance, and no entry can be dated inside a closed month.
5. Every change goes in the audit log with before and after values.

Stage 1 implements rule 5 and the role model. Stage 2 implements rules 1, 3 and 4 in `backend/app/services/ledger.py`, each covered by a test in `backend/tests/test_ledger.py`. Rule 2 arrives with invoices in stage 3.

## Roles

| Role | Can | Cannot |
|---|---|---|
| Owner | Everything | |
| Accountant | All accounting, invoicing, bills, payments, reports, period close | Settings, users, payroll |
| Sales | Contacts, quotes, sales invoices, see stock levels | Payments, purchase prices, ledger, payroll |
| Stores | Receive goods, stock movements, see purchase orders | Sales prices, payments, ledger |
| HR | Employees, leave, payroll | Invoices, bills, ledger |
| Viewer | Dashboards and reports | Change anything |

## Development

Backend tests run against a local PostgreSQL:

```bash
cd backend
pip install ".[dev]"
createdb erp_test
DATABASE_URL=postgresql+psycopg://erp:erp@localhost:5432/erp_test pytest
ruff check . && ruff format --check .
```

Frontend:

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173, expects the API on :8000
npm run lint && npm run build
```

CI runs all of the above on every push.

## Licence

MIT. See [LICENSE](LICENSE).
