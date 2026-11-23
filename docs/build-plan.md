# Build plan

Each stage ends with something you can log into and use. Each stage is a GitHub milestone.

| Stage | What is built | Done when |
|---|---|---|
| 1 | Shared core: Docker, database, login, users, roles, audit log, company settings, CI | Owner can log in, add users, see the audit log. Tests green. |
| 2 | Chart of accounts, journal entries and lines, balance rule, period close and lock, trial balance | Opening balances entered and trial balance agrees with the accountant |
| 3 | Contacts, items, quotes, sales invoices, customer payments, debtors ageing | A real month of invoicing done in the system |
| 4 | Purchase orders, receiving, bills, supplier payments, stock movements, stock valuation | Stock count matches the system |
| 5 | Bank accounts, statement CSV import, reconciliation, profit and loss, balance sheet | First month closed and reconciled |
| 6 | Employees, leave, payroll with PASI, WPS bank file, payslip PDF | One payroll run checked line by line, then a second run paid from the system |
| 7 | Dashboard, email reminders, scheduled jobs, VAT switch tested with a dummy company | Team using it daily |

The full design is in [design-spec.md](design-spec.md).
