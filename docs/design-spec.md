**Four Peaks Trading And Contracting LLC**

ERP design specification

Version 0.1, 18 November 2026

Prepared by Yashfeen

**Contents**

**1. Purpose** 3

**2. Goals and non-goals** 3

> 2.1 Goals 3
>
> 2.2 Non-goals for version 1 3

**3. Users and roles** 3

**4. How the system is organised** 4

**5. Data model** 4

> 5.1 Shared core 4
>
> 5.2 Sales and CRM 5
>
> 5.3 Inventory and purchasing 6
>
> 5.4 Accounting 7
>
> 5.5 HR and payroll 7

**6. Screens** 8

**7. Rules that apply everywhere** 8

**8. Build plan** 9

**9. Standard chart of accounts** 9

**10. Open questions** 10

# 1. Purpose

This document describes the ERP system we will build for Four Peaks
Trading And Contracting LLC. It covers what the system does, who uses
it, how the data is organised and the rules each part of the system
follows. It is written so that anyone on the team can read it, and so
that it can be handed to a developer (human or AI) as the brief for
building it.

The company sells both physical products and services, is registered in
Oman, and currently handles fewer than fifty invoices and transactions a
month. Turnover is below the VAT registration threshold, so VAT is
designed in but switched off. The system is built for a team of two to
ten people.

# 2. Goals and non-goals

## 2.1 Goals

- Keep one set of accurate books that an accountant or auditor can
  trust.

- Issue invoices, record bills and track who owes what without
  spreadsheets.

- Know what stock is on hand and what it cost.

- Keep customer and supplier details in one place.

- Run monthly payroll and produce payslips and a bank payment file.

- Let each team member see and do only what their role allows, with
  every change logged.

## 2.2 Non-goals for version 1

- Multiple currencies. Everything is in Omani rial.

- Multiple warehouses or locations.

- Fixed assets and depreciation.

- Approval workflows. Roles control access, not sign-off chains.

- Manufacturing, bills of materials or projects with time tracking.

Each of these can be added later. The data model is laid out so that
none of them requires rebuilding the core.

# 3. Users and roles

Every person has a login. A person has exactly one role, and the role
decides which screens they can open and which actions they can take.

|            |                                                                           |                                                               |
|------------|---------------------------------------------------------------------------|---------------------------------------------------------------|
| **Role**   | **Can do**                                                                | **Cannot do**                                                 |
| Owner      | Everything, including settings, period close, user management and payroll | Nothing is blocked                                            |
| Accountant | All accounting, invoicing, bills, payments, reports and period close      | Change settings, manage users, see payroll                    |
| Sales      | Create and edit contacts, quotes and sales invoices; see stock levels     | Post payments, see purchase prices, see payroll or the ledger |
| Stores     | Receive goods, record stock movements, see purchase orders                | See sales prices, payments or the ledger                      |
| HR         | Manage employees, leave and payroll                                       | See invoices, bills or the ledger                             |
| Viewer     | See dashboards and reports                                                | Change anything                                               |

The audit log records who did what and when for every create, edit,
delete, post and period close. Entries in the log cannot be edited or
deleted by anyone.

# 4. How the system is organised

The system has four modules sitting on one shared core, all reading and
writing one database.

- Shared core. Logins, roles, audit log, company settings, number
  sequences, chart of accounts and the general ledger.

- Sales and CRM. Contacts, quotes, sales invoices, customer payments.

- Inventory and purchasing. Items, stock levels, stock movements,
  purchase orders, purchase bills, supplier payments.

- Accounting. Journal entries, bank accounts, reports, period close, VAT
  (switched off).

- HR and payroll. Employees, leave, salary structure, monthly payroll,
  payslips, bank file.

The single most important rule is that every event that moves money
creates a journal entry in the general ledger. Invoices, bills, payments
and payslips are all sources of journal entries, and every report is
built from the ledger alone. This is what keeps the books consistent no
matter which module the money came through.

# 5. Data model

All tables share four housekeeping fields which are not repeated below.
These are a unique id, created at, created by and updated at. Money is
stored as a decimal with three decimal places because the rial is
divided into one thousand baisa. Quantities are decimals with three
places too, so items sold by weight or length work.

## 5.1 Shared core

### Users

|               |           |                                                        |
|---------------|-----------|--------------------------------------------------------|
| **Field**     | **Type**  | **Notes**                                              |
| name          | text      |                                                        |
| email         | text      | Used to log in, unique                                 |
| password hash | text      | Never stored in plain text                             |
| role          | choice    | One of the six roles in section 3                      |
| active        | yes or no | Deactivated users keep their history but cannot log in |

### Accounts (chart of accounts)

|           |                 |                                           |
|-----------|-----------------|-------------------------------------------|
| **Field** | **Type**        | **Notes**                                 |
| code      | text            | Four digits, unique, e.g. 1100            |
| name      | text            | e.g. Bank, Trade debtors                  |
| type      | choice          | Asset, liability, equity, income, expense |
| parent    | link to account | Optional, for grouping in reports         |
| active    | yes or no       |                                           |

The system ships with a standard small-company chart of accounts
(section 9) and the owner can add accounts.

### Journal entries and journal lines

A journal entry is one balanced set of debits and credits. It has an
entry date, a source (manual, sales invoice, purchase bill, payment,
payroll, stock adjustment), a link to the source record, a short
narration and a locked flag. Its lines each name an account, a debit
amount and a credit amount, and may carry an optional link to a contact.
The debits of an entry must equal its credits, and the system refuses to
save an entry that does not balance.

### Settings

Company name, address, commercial registration number, VAT registration
number (blank until registered), VAT enabled (off), financial year start
month, default accounts for each kind of posting, and the next number
for each sequence (quotes, invoices, bills, payments, payslips).

### Audit log

User, time, action, table, record id, and the before and after values as
text.

## 5.2 Sales and CRM

### Contacts

|                |          |                            |
|----------------|----------|----------------------------|
| **Field**      | **Type** | **Notes**                  |
| name           | text     |                            |
| type           | choice   | Customer, supplier or both |
| contact person | text     |                            |
| phone, email   | text     |                            |
| address        | text     |                            |
| VAT number     | text     | Optional                   |
| payment terms  | number   | Days until due, default 30 |
| notes          | text     | Free text for the CRM side |

One contacts table serves both customers and suppliers because small
companies often buy from and sell to the same business. The type field
controls which lists a contact appears in.

### Quotes

Number, contact, date, valid until, status (draft, sent, accepted,
declined, expired), lines. A quote never touches stock or the ledger. An
accepted quote can be converted to a sales invoice with one click, and
the invoice keeps a link back to it.

### Sales invoices

|                      |          |                                            |
|----------------------|----------|--------------------------------------------|
| **Field**            | **Type** | **Notes**                                  |
| number               | text     | Sequential, no gaps, e.g. INV-2026-0001    |
| contact              | link     |                                            |
| issue date, due date | date     | Due date defaults from the contact's terms |
| status               | choice   | Draft, issued, part paid, paid, cancelled  |
| subtotal, VAT, total | money    | Calculated from lines                      |
| amount paid          | money    | Sum of allocated payments                  |
| journal entry        | link     | Set when issued                            |

Each line has an item, description, quantity, unit price, VAT category
and line total. Issuing an invoice is the moment it becomes real. It
gets its number, posts to the ledger (debit trade debtors, credit sales,
and credit VAT output if VAT is on), and for each product line creates a
stock movement out. A draft can be edited freely. An issued invoice
cannot be edited, only cancelled, which reverses its journal entry and
stock movements and leaves both the original and the reversal visible.

### Customer activity

The contact screen shows every quote, invoice and payment for that
contact plus a simple timeline of notes that any user with sales access
can add. This is the whole of the CRM for version 1, and it is enough
for a team this size.

## 5.3 Inventory and purchasing

### Items

|                                 |          |                                                         |
|---------------------------------|----------|---------------------------------------------------------|
| **Field**                       | **Type** | **Notes**                                               |
| code, name                      | text     |                                                         |
| kind                            | choice   | Product or service                                      |
| unit                            | text     | Each, kg, hour, etc.                                    |
| sales price                     | money    |                                                         |
| cost price                      | money    | Last purchase cost, updated on receipt                  |
| VAT category                    | choice   | Standard 5%, zero rated, exempt                         |
| quantity on hand                | quantity | Products only, always equals the sum of stock movements |
| reorder level                   | quantity | Optional, used for the low stock list                   |
| income account, expense account | link     | Defaults from settings                                  |

### Stock movements

Item, date, quantity (positive in, negative out), unit cost, reason
(purchase receipt, sale, adjustment, return), link to the source record.
Quantity on hand is never typed in directly. It is always the sum of
movements, and a stock count is recorded as an adjustment movement for
the difference. Stock is valued at weighted average cost, which is
simple and acceptable for a company this size.

### Purchase orders

Number, supplier, date, expected date, status (draft, sent, part
received, received, cancelled), lines. A purchase order does not touch
stock or the ledger. Receiving goods against it creates stock movements
in and updates the item cost. Receiving can be partial.

### Purchase bills

Number (the supplier's own invoice number plus our internal sequence),
supplier, bill date, due date, status, lines, totals, journal entry.
Recording a bill posts debit expense or stock, credit trade creditors,
and debit VAT input if VAT is on. A bill can be created from a received
purchase order so the lines are not typed twice.

## 5.4 Accounting

### Payments

Date, direction (in or out), contact, bank account, amount, method (bank
transfer, cash, card), reference, and allocations to one or more
invoices or bills. Recording a payment posts debit bank and credit trade
debtors for money in, or debit trade creditors and credit bank for money
out. A payment can be left unallocated and matched later.
Over-allocation is refused.

### Bank accounts

Name, bank, account number, linked ledger account, opening balance. The
bank reconciliation screen lists ledger transactions for a bank account
and lets the accountant tick them off against a bank statement, with a
running difference shown. Statement import from a CSV file is included;
automatic bank feeds are not.

### Manual journal entries

For anything the other modules do not cover (owner's drawings, accruals,
corrections). Same balancing rule as every other entry.

### Period close

The owner or accountant closes a month. Closing sets the locked flag on
every journal entry dated in that month, and the system then refuses any
edit, cancellation or new entry dated inside a closed month. Corrections
to a closed month are made as new entries in the current month. A closed
month can be reopened by the owner only, and that action is logged.

### VAT

VAT is switched off in settings. While off, the VAT category on items is
kept but ignored, invoices show no VAT line, and the VAT accounts
receive no postings. When the company registers, the owner enters the
VAT number, turns VAT on, and from that date invoices show VAT at the
item's category rate and the quarterly VAT return report becomes
available. Nothing already posted is touched.

## 5.5 HR and payroll

### Employees

|                                         |               |                                                  |
|-----------------------------------------|---------------|--------------------------------------------------|
| **Field**                               | **Type**      | **Notes**                                        |
| name, nationality, civil id or passport | text          |                                                  |
| job title, start date, end date         | text and date |                                                  |
| basic salary                            | money         | Monthly                                          |
| allowances                              | list          | Housing, transport, other, each a monthly amount |
| bank name, account number               | text          | For the bank payment file                        |
| PASI member                             | yes or no     | Omani nationals only                             |
| annual leave days                       | number        | Default 30                                       |

Only the owner and the HR role can open employee records. Salary figures
are never shown on any other screen or report except the payroll journal
summary in the ledger, which shows totals only.

### Leave

Employee, type (annual, sick, unpaid, other), from, to, days, status
(requested, approved, rejected). Unpaid leave reduces that month's pay
in proportion to working days. The balance of annual leave is shown on
the employee record.

### Payroll runs and payslips

A payroll run covers one month. Creating it generates a payslip for
every active employee with gross pay (basic plus allowances), deductions
(unpaid leave, employee PASI contribution where applicable, any advance
recovery), employer PASI contribution, and net pay. The HR user reviews,
adjusts individual payslips if needed, and posts the run. Posting
creates one journal entry (debit salary expense and employer PASI
expense, credit salaries payable and PASI payable) and locks the
payslips. Paying the run creates a payment and produces a bank file in
the format the company's bank accepts for WPS. Payslips can be printed
or sent by email as PDF.

PASI rates and any other statutory figures are stored in settings with
an effective date, not written into the code, so they can be updated
when they change.

# 6. Screens

The list below is every screen in version 1. Mockups of the ones marked
with an asterisk will be produced next, because they are the ones people
will spend most of their day in.

|            |                                                                                                                                                                                                 |
|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Module** | **Screens**                                                                                                                                                                                     |
| Core       | Login, dashboard \*, settings, users, chart of accounts, audit log                                                                                                                              |
| Sales      | Contacts list, contact page \*, quotes list, quote form, invoices list, invoice form \*, record payment                                                                                         |
| Inventory  | Items list, item page, stock movements, stock count, low stock, purchase orders list, purchase order form, receive goods, bills list, bill form \*                                              |
| Accounting | Journal, manual entry, bank accounts, bank reconciliation, period close, reports (profit and loss, balance sheet, trial balance, debtors ageing, creditors ageing, VAT return, stock valuation) |
| HR         | Employees list, employee page, leave, payroll run \*, payslip                                                                                                                                   |

The dashboard shows cash in bank, money owed to us, money we owe, this
month's sales and expenses, overdue invoices, and low stock. Each role
sees only the tiles it is allowed to.

# 7. Rules that apply everywhere

1.  Nothing that has been posted is ever edited. It is reversed and
    re-done, and both are kept.

2.  Every number sequence runs without gaps. Cancelled documents keep
    their number.

3.  Quantity on hand and every account balance are always derived from
    movements and lines, never stored and adjusted by hand.

4.  Every save checks that journal entries balance and that the date is
    not in a closed month.

5.  Every change is in the audit log with before and after values.

6.  Amounts are shown to three decimal places with the OMR symbol, dates
    as day month year, and the interface is in English with Arabic field
    labels available on printed invoices.

7.  Daily automatic backup of the database kept for ninety days, with a
    tested restore procedure.

# 8. Build plan

The order below means each stage produces something usable, and the
riskiest piece (payroll) comes last after the rest has been running for
a while.

|           |                                                                                       |                                                                                                         |
|-----------|---------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Stage** | **What is built**                                                                     | **Done when**                                                                                           |
| 1         | Shared core, chart of accounts, journal, manual entries, trial balance                | Opening balances entered and trial balance agrees with the accountant                                   |
| 2         | Contacts, items, sales invoices, customer payments, debtors ageing                    | A real month of invoicing done in the system                                                            |
| 3         | Purchase orders, receiving, bills, supplier payments, stock reports                   | Stock count matches the system                                                                          |
| 4         | Bank reconciliation, period close, profit and loss, balance sheet                     | First month closed and reconciled                                                                       |
| 5         | Employees, leave, payroll, bank file                                                  | One payroll run checked line by line against the current method, then a second run paid from the system |
| 6         | Dashboard, email sending, scheduled reminders, VAT switch tested with a dummy company | Team using it daily without the old spreadsheets                                                        |

Tools by stage. Design and mockups here in Claude. Database schema and
all application code in Claude Code against a GitHub repository, with
automated tests for the posting rules and the balance checks. A first
clickable prototype of the invoice screen as a published artifact so the
team can try it. Scheduled tasks for the monthly overdue-invoice and
low-stock emails once the system is live.

# 9. Standard chart of accounts

|          |                              |           |
|----------|------------------------------|-----------|
| **Code** | **Name**                     | **Type**  |
| 1000     | Cash                         | Asset     |
| 1100     | Bank                         | Asset     |
| 1200     | Trade debtors                | Asset     |
| 1300     | Stock                        | Asset     |
| 1400     | VAT input                    | Asset     |
| 1500     | Prepayments and advances     | Asset     |
| 2000     | Trade creditors              | Liability |
| 2100     | VAT output                   | Liability |
| 2200     | Salaries payable             | Liability |
| 2300     | PASI payable                 | Liability |
| 2400     | Other payables               | Liability |
| 3000     | Owner's capital              | Equity    |
| 3100     | Owner's drawings             | Equity    |
| 3200     | Retained earnings            | Equity    |
| 4000     | Sales of products            | Income    |
| 4100     | Sales of services            | Income    |
| 4900     | Other income                 | Income    |
| 5000     | Cost of goods sold           | Expense   |
| 5100     | Stock adjustments            | Expense   |
| 6000     | Salaries and wages           | Expense   |
| 6100     | Employer PASI                | Expense   |
| 6200     | Rent                         | Expense   |
| 6300     | Utilities and telecoms       | Expense   |
| 6400     | Transport and vehicles       | Expense   |
| 6500     | Marketing                    | Expense   |
| 6600     | Professional fees            | Expense   |
| 6700     | Bank charges                 | Expense   |
| 6800     | Government fees and licences | Expense   |
| 6900     | Other expenses               | Expense   |

# 10. Open questions

- Which bank does the company use, so the WPS file format can be
  confirmed.

- Whether any staff are paid partly in cash, which changes how the
  payment is recorded.

- Whether invoices need to be bilingual (Arabic and English) from day
  one.

- Whether the accountant wants the trial balance in a particular export
  format.
