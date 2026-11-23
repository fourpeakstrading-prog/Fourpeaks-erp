"""Standard small-company chart of accounts (spec section 9).

Each tuple: code, name, type, system_key. The system key is how other modules
find the account they post to, so it never depends on a code the owner may rename.
"""

STARTER_CHART: list[tuple[str, str, str, str | None]] = [
    ("1000", "Cash", "asset", "cash"),
    ("1100", "Bank", "asset", "bank"),
    ("1200", "Trade debtors", "asset", "debtors"),
    ("1300", "Stock", "asset", "stock"),
    ("1400", "VAT input", "asset", "vat_input"),
    ("1500", "Prepayments and advances", "asset", None),
    ("2000", "Trade creditors", "liability", "creditors"),
    ("2100", "VAT output", "liability", "vat_output"),
    ("2200", "Salaries payable", "liability", "salaries_payable"),
    ("2300", "PASI payable", "liability", "pasi_payable"),
    ("2400", "Other payables", "liability", None),
    ("3000", "Owner's capital", "equity", "capital"),
    ("3100", "Owner's drawings", "equity", None),
    ("3200", "Retained earnings", "equity", "retained_earnings"),
    ("4000", "Sales of products", "income", "sales_products"),
    ("4100", "Sales of services", "income", "sales_services"),
    ("4900", "Other income", "income", None),
    ("5000", "Cost of goods sold", "expense", "cogs"),
    ("5100", "Stock adjustments", "expense", "stock_adjustments"),
    ("6000", "Salaries and wages", "expense", "salaries"),
    ("6100", "Employer PASI", "expense", "employer_pasi"),
    ("6200", "Rent", "expense", None),
    ("6300", "Utilities and telecoms", "expense", None),
    ("6400", "Transport and vehicles", "expense", None),
    ("6500", "Marketing", "expense", None),
    ("6600", "Professional fees", "expense", None),
    ("6700", "Bank charges", "expense", "bank_charges"),
    ("6800", "Government fees and licences", "expense", None),
    ("6900", "Other expenses", "expense", None),
]
