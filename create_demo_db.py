"""Creates data/demo.db — a realistic demo database for screenshots.

Covers the full month of September 2026 for a single-person household
in a German city. Run once:

    venv\Scripts\python create_demo_db.py
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import database as db

DEMO_PATH = Path(__file__).parent / "data" / "demo.db"


def run():
    DEMO_PATH.parent.mkdir(exist_ok=True)
    if DEMO_PATH.exists():
        DEMO_PATH.unlink()

    conn = sqlite3.connect(DEMO_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(db.SCHEMA)

    # ── Accounts ──────────────────────────────────────────────────────────────
    account_rows = [
        ("SPARKASSE",   "bank",        452130, "2026-09-01"),
        ("ING",         "bank",        820000, "2026-09-01"),
        ("REVOLUT",     "bank",         34250, "2026-09-01"),
        ("DKB",         "bank",        110000, "2026-09-01"),
        ("VISA",        "credit_card",      0, "2026-09-01"),
        ("CASH",        "cash",          8500, "2026-09-01"),
    ]
    for label, atype, opening, date in account_rows:
        conn.execute(
            "INSERT INTO accounts (label, account_type, opening_balance_cents, opening_date) "
            "VALUES (?,?,?,?)",
            (label, atype, opening, date),
        )

    # ── Categories ────────────────────────────────────────────────────────────
    for name in db.DEFAULT_EXPENSE_CATEGORIES:
        conn.execute(
            "INSERT INTO categories (name, transaction_type) VALUES (?, 'expense')", (name,)
        )
    for name in db.DEFAULT_INCOME_CATEGORIES:
        conn.execute(
            "INSERT INTO categories (name, transaction_type) VALUES (?, 'income')", (name,)
        )

    # ── Settings ──────────────────────────────────────────────────────────────
    conn.execute("INSERT INTO settings (key, value) VALUES ('tracking_start_date', '2026-09-01')")
    conn.execute("INSERT INTO settings (key, value) VALUES ('app_title', 'Expense Monitor')")

    conn.commit()

    # Lookup helpers
    A = {r["label"]: r["id"] for r in conn.execute("SELECT label, id FROM accounts")}
    C = {r["name"]:  r["id"] for r in conn.execute("SELECT name,  id FROM categories")}

    # ── Transactions — September 2026 ─────────────────────────────────────────
    # (date, type, cents, from_label, to_label, category, description)
    # None → NULL
    txns = [
        # ── Income ────────────────────────────────────────────────────────────
        ("2026-09-01", "INCOME",  320000, None,         "SPARKASSE", "Salary",        "September salary"),
        ("2026-09-15", "INCOME",    1850, None,         "ING",       "Interest",      "Savings interest"),

        # ── Fixed costs ───────────────────────────────────────────────────────
        ("2026-09-01", "EXPENSE", 105000, "SPARKASSE",  None,        "Housing and bills", "Rent — September"),
        ("2026-09-03", "EXPENSE",   4999, "SPARKASSE",  None,        "Housing and bills", "Telekom — internet"),
        ("2026-09-03", "EXPENSE",   7850, "SPARKASSE",  None,        "Housing and bills", "Vattenfall — electricity"),
        ("2026-09-04", "EXPENSE",   1836, "SPARKASSE",  None,        "Housing and bills", "GEZ broadcasting fee"),
        ("2026-09-01", "EXPENSE",   3500, "SPARKASSE",  None,        "Subscriptions",     "Gym membership"),
        ("2026-09-01", "EXPENSE",   1299, "VISA",       None,        "Subscriptions",     "Netflix"),
        ("2026-09-01", "EXPENSE",    999, "VISA",       None,        "Subscriptions",     "Spotify"),
        ("2026-09-01", "EXPENSE",     99, "REVOLUT",    None,        "Subscriptions",     "iCloud 50 GB"),
        ("2026-09-01", "EXPENSE",   4900, "SPARKASSE",  None,        "Transport",         "Deutschlandticket"),

        # ── Groceries ─────────────────────────────────────────────────────────
        ("2026-09-02", "EXPENSE",   6743, "VISA",       None,        "Groceries",     "REWE — weekly shop"),
        ("2026-09-06", "EXPENSE",   3821, "CASH",       None,        "Groceries",     "Aldi"),
        ("2026-09-09", "EXPENSE",   5487, "VISA",       None,        "Groceries",     "REWE"),
        ("2026-09-13", "EXPENSE",   2891, "CASH",       None,        "Groceries",     "Lidl"),
        ("2026-09-16", "EXPENSE",   7234, "VISA",       None,        "Groceries",     "REWE — weekly shop"),
        ("2026-09-20", "EXPENSE",   4555, "CASH",       None,        "Groceries",     "Aldi"),
        ("2026-09-23", "EXPENSE",   6187, "VISA",       None,        "Groceries",     "REWE"),
        ("2026-09-27", "EXPENSE",   3344, "CASH",       None,        "Groceries",     "Lidl"),
        ("2026-09-30", "EXPENSE",   4892, "VISA",       None,        "Groceries",     "REWE"),

        # ── Eating out ────────────────────────────────────────────────────────
        ("2026-09-04", "EXPENSE",    890, "CASH",       None,        "Eating out",    "Burgermeister"),
        ("2026-09-07", "EXPENSE",   1450, "CASH",       None,        "Eating out",    "Café Einstein — lunch"),
        ("2026-09-11", "EXPENSE",   3480, "VISA",       None,        "Eating out",    "Ristorante da Mario"),
        ("2026-09-14", "EXPENSE",    550, "CASH",       None,        "Eating out",    "Döner"),
        ("2026-09-18", "EXPENSE",   2290, "REVOLUT",    None,        "Eating out",    "Thai Garden"),
        ("2026-09-21", "EXPENSE",    480, "CASH",       None,        "Eating out",    "Coffee & Kuchen"),
        ("2026-09-25", "EXPENSE",   5890, "VISA",       None,        "Eating out",    "Birthday dinner — Zur Linde"),
        ("2026-09-28", "EXPENSE",   3250, "REVOLUT",    None,        "Eating out",    "Sakura Sushi"),

        # ── Transport ─────────────────────────────────────────────────────────
        ("2026-09-08", "EXPENSE",   7234, "VISA",       None,        "Transport",     "Shell — fuel"),
        ("2026-09-19", "EXPENSE",    450, "CASH",       None,        "Transport",     "Parking — city centre"),
        ("2026-09-24", "EXPENSE",   1860, "REVOLUT",    None,        "Transport",     "Taxi — airport"),

        # ── Health ────────────────────────────────────────────────────────────
        ("2026-09-10", "EXPENSE",   2340, "VISA",       None,        "Health",        "DM pharmacy"),
        ("2026-09-17", "EXPENSE",   1250, "CASH",       None,        "Health",        "Prescription"),
        ("2026-09-26", "EXPENSE",   8000, "SPARKASSE",  None,        "Health",        "Dentist"),

        # ── Shopping ──────────────────────────────────────────────────────────
        ("2026-09-05", "EXPENSE",   4999, "VISA",       None,        "Shopping",      "Amazon — books"),
        ("2026-09-12", "EXPENSE",   7990, "VISA",       None,        "Shopping",      "Zara — jacket"),
        ("2026-09-19", "EXPENSE",   2499, "REVOLUT",    None,        "Shopping",      "Müller — household"),
        ("2026-09-23", "EXPENSE",  14990, "VISA",       None,        "Shopping",      "MediaMarkt — headphones"),
        ("2026-09-29", "EXPENSE",   1850, "VISA",       None,        "Shopping",      "Tchibo"),

        # ── Transfers ─────────────────────────────────────────────────────────
        ("2026-09-01", "TRANSFER",  50000, "SPARKASSE", "ING",       None,            "Monthly savings"),
        ("2026-09-05", "TRANSFER",  10000, "SPARKASSE", "CASH",      None,            "ATM withdrawal"),
        ("2026-09-15", "TRANSFER",   6000, "SPARKASSE", "CASH",      None,            "ATM withdrawal"),
        ("2026-09-20", "TRANSFER",  10000, "SPARKASSE", "REVOLUT",   None,            "Top up Revolut"),
        ("2026-09-28", "TRANSFER",  85000, "SPARKASSE", "VISA",      None,            "VISA card payment"),
    ]

    for date, ttype, cents, from_lbl, to_lbl, cat, desc in txns:
        conn.execute(
            "INSERT INTO transactions "
            "(date, transaction_type, amount_cents, from_account_id, to_account_id, category_id, description) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                date, ttype, cents,
                A.get(from_lbl) if from_lbl else None,
                A.get(to_lbl)   if to_lbl   else None,
                C.get(cat)      if cat       else None,
                desc,
            ),
        )

    conn.commit()
    conn.close()
    print(f"Demo database created: {DEMO_PATH}")
    print(f"Run with:  run_demo.bat")


if __name__ == "__main__":
    run()
