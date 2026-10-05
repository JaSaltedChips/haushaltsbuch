"""SQLite database layer — schema, CRUD, and balance calculations."""

from __future__ import annotations

import sqlite3
import calendar
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, List, Optional

DB_DIR = Path(__file__).parent / "data"
DB_PATH = DB_DIR / "expense_monitor.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL UNIQUE,
    account_type TEXT NOT NULL CHECK(account_type IN ('bank', 'cash', 'credit_card')),
    opening_balance_cents INTEGER NOT NULL DEFAULT 0,
    opening_date TEXT NOT NULL DEFAULT '2026-10-04',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('expense', 'income')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(name, transaction_type)
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('EXPENSE', 'INCOME', 'TRANSFER')),
    amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
    from_account_id INTEGER REFERENCES accounts(id),
    to_account_id INTEGER REFERENCES accounts(id),
    category_id INTEGER REFERENCES categories(id),
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tx_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_tx_type ON transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_tx_from ON transactions(from_account_id);
CREATE INDEX IF NOT EXISTS idx_tx_to ON transactions(to_account_id);
"""

DEFAULT_ACCOUNTS = [
    ("BANK-1", "bank"),
    ("BANK-2", "bank"),
    ("BANK-3", "bank"),
    ("BANK-4", "bank"),
    ("CARD", "credit_card"),
    ("CASH", "cash"),
]

DEFAULT_EXPENSE_CATEGORIES = [
    "Groceries", "Eating out", "Transport", "Housing and bills",
    "Shopping", "Health", "Travel", "Subscriptions", "To India", "Other",
]

DEFAULT_INCOME_CATEGORIES = [
    "Salary", "Interest", "Bonus", "Dividends", "Other income",
]

DEFAULT_SETTINGS = {
    "tracking_start_date": "2026-10-04",
    "app_title": "Expense Monitor",
}


def init_db():
    DB_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        _seed_defaults(conn)
        conn.commit()
    finally:
        conn.close()


def _seed_defaults(conn):
    if conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] == 0:
        for label, atype in DEFAULT_ACCOUNTS:
            conn.execute(
                "INSERT OR IGNORE INTO accounts (label, account_type, opening_balance_cents, opening_date) VALUES (?, ?, 0, '2026-10-04')",
                (label, atype),
            )

    if conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
        for name in DEFAULT_EXPENSE_CATEGORIES:
            conn.execute("INSERT OR IGNORE INTO categories (name, transaction_type) VALUES (?, 'expense')", (name,))
        for name in DEFAULT_INCOME_CATEGORIES:
            conn.execute("INSERT OR IGNORE INTO categories (name, transaction_type) VALUES (?, 'income')", (name,))

    for key, value in DEFAULT_SETTINGS.items():
        conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Accounts ──────────────────────────────────────────────────────────────────

def get_accounts(conn, active_only=True, as_of_date: Optional[str] = None):
    query = "SELECT * FROM accounts"
    if active_only:
        query += " WHERE is_active = 1"
    query += " ORDER BY CASE account_type WHEN 'bank' THEN 1 WHEN 'cash' THEN 2 ELSE 3 END, label"
    rows = conn.execute(query).fetchall()
    result = []
    for row in rows:
        acc = dict(row)
        acc["balance_cents"] = _compute_balance(conn, acc, as_of_date)
        result.append(acc)
    return result


def get_account(conn, account_id: int) -> Optional[dict]:
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    if not row:
        return None
    acc = dict(row)
    acc["balance_cents"] = _compute_balance(conn, acc)
    return acc


def _compute_balance(conn, account: dict, as_of_date: Optional[str] = None) -> int:
    aid = account["id"]
    opening = account["opening_balance_cents"]
    date_clause = " AND date <= ?" if as_of_date else ""
    extra = (as_of_date,) if as_of_date else ()

    def q(sql, *args):
        return conn.execute(sql, args + extra).fetchone()[0]

    if account["account_type"] == "credit_card":
        expenses = q(
            f"SELECT COALESCE(SUM(amount_cents),0) FROM transactions WHERE from_account_id=? AND transaction_type='EXPENSE'{date_clause}",
            aid,
        )
        payments = q(
            f"SELECT COALESCE(SUM(amount_cents),0) FROM transactions WHERE to_account_id=? AND transaction_type='TRANSFER'{date_clause}",
            aid,
        )
        return opening + expenses - payments
    else:
        income_in = q(
            f"SELECT COALESCE(SUM(amount_cents),0) FROM transactions WHERE to_account_id=? AND transaction_type='INCOME'{date_clause}",
            aid,
        )
        transfers_in = q(
            f"SELECT COALESCE(SUM(amount_cents),0) FROM transactions WHERE to_account_id=? AND transaction_type='TRANSFER'{date_clause}",
            aid,
        )
        expenses_out = q(
            f"SELECT COALESCE(SUM(amount_cents),0) FROM transactions WHERE from_account_id=? AND transaction_type='EXPENSE'{date_clause}",
            aid,
        )
        transfers_out = q(
            f"SELECT COALESCE(SUM(amount_cents),0) FROM transactions WHERE from_account_id=? AND transaction_type='TRANSFER'{date_clause}",
            aid,
        )
        return opening + income_in + transfers_in - expenses_out - transfers_out


def create_account(conn, label: str, account_type: str, opening_balance_cents: int = 0, opening_date: str = "2026-10-04") -> int:
    cur = conn.execute(
        "INSERT INTO accounts (label, account_type, opening_balance_cents, opening_date) VALUES (?, ?, ?, ?)",
        (label, account_type, opening_balance_cents, opening_date),
    )
    return cur.lastrowid


def update_account(conn, account_id: int, **kwargs):
    allowed = {"label", "account_type", "opening_balance_cents", "opening_date", "is_active"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return
    sets = ", ".join(f"{k} = ?" for k in updates)
    conn.execute(f"UPDATE accounts SET {sets} WHERE id = ?", [*updates.values(), account_id])


def delete_account(conn, account_id: int):
    count = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE from_account_id = ? OR to_account_id = ?",
        (account_id, account_id),
    ).fetchone()[0]
    if count > 0:
        raise ValueError(f"Cannot delete: {count} transaction(s) reference this account. Deactivate it instead.")
    conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))


# ── Categories ────────────────────────────────────────────────────────────────

def get_categories(conn, transaction_type: Optional[str] = None) -> List[dict]:
    if transaction_type:
        rows = conn.execute(
            "SELECT * FROM categories WHERE transaction_type = ? ORDER BY name",
            (transaction_type,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM categories ORDER BY transaction_type, name"
        ).fetchall()
    return [dict(r) for r in rows]


def create_category(conn, name: str, transaction_type: str) -> int:
    cur = conn.execute(
        "INSERT INTO categories (name, transaction_type) VALUES (?, ?)",
        (name, transaction_type),
    )
    return cur.lastrowid


def update_category(conn, category_id: int, name: str):
    conn.execute("UPDATE categories SET name = ? WHERE id = ?", (name, category_id))


def delete_category(conn, category_id: int):
    count = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE category_id = ?",
        (category_id,),
    ).fetchone()[0]
    if count > 0:
        raise ValueError(f"Cannot delete: {count} transaction(s) use this category.")
    conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))


# ── Transactions ──────────────────────────────────────────────────────────────

_TX_SELECT = """
    SELECT
        t.id, t.date, t.transaction_type, t.amount_cents, t.description, t.created_at,
        t.from_account_id, fa.label AS from_account_label, fa.account_type AS from_account_type,
        t.to_account_id, ta.label AS to_account_label, ta.account_type AS to_account_type,
        t.category_id, c.name AS category_name
    FROM transactions t
    LEFT JOIN accounts fa ON t.from_account_id = fa.id
    LEFT JOIN accounts ta ON t.to_account_id = ta.id
    LEFT JOIN categories c ON t.category_id = c.id
"""


def get_transactions(
    conn,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    transaction_type: Optional[str] = None,
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
) -> List[dict]:
    conditions, params = [], []

    if date_from:
        conditions.append("t.date >= ?"); params.append(date_from)
    if date_to:
        conditions.append("t.date <= ?"); params.append(date_to)
    if transaction_type:
        conditions.append("t.transaction_type = ?"); params.append(transaction_type)
    if account_id:
        conditions.append("(t.from_account_id = ? OR t.to_account_id = ?)")
        params += [account_id, account_id]
    if category_id:
        conditions.append("t.category_id = ?"); params.append(category_id)
    if search:
        conditions.append("(t.description LIKE ? OR fa.label LIKE ? OR ta.label LIKE ? OR c.name LIKE ?)")
        s = f"%{search}%"; params += [s, s, s, s]

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    query = f"{_TX_SELECT} {where} ORDER BY t.date DESC, t.id DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    return [dict(r) for r in conn.execute(query, params).fetchall()]


def get_transaction(conn, tx_id: int) -> Optional[dict]:
    row = conn.execute(f"{_TX_SELECT} WHERE t.id = ?", (tx_id,)).fetchone()
    return dict(row) if row else None


def create_transaction(
    conn,
    date: str,
    transaction_type: str,
    amount_cents: int,
    from_account_id: Optional[int] = None,
    to_account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    description: str = "",
) -> int:
    validate_transaction(conn, transaction_type, amount_cents, from_account_id, to_account_id)
    cur = conn.execute(
        "INSERT INTO transactions (date, transaction_type, amount_cents, from_account_id, to_account_id, category_id, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (date, transaction_type, amount_cents, from_account_id, to_account_id, category_id, description),
    )
    return cur.lastrowid


def update_transaction(conn, tx_id: int, **kwargs):
    allowed = {"date", "transaction_type", "amount_cents", "from_account_id", "to_account_id", "category_id", "description"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return
    current = conn.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,)).fetchone()
    if not current:
        raise ValueError(f"Transaction {tx_id} not found")
    merged = {**dict(current), **updates}
    validate_transaction(
        conn,
        merged["transaction_type"],
        merged["amount_cents"],
        merged.get("from_account_id"),
        merged.get("to_account_id"),
    )
    sets = ", ".join(f"{k} = ?" for k in updates)
    conn.execute(f"UPDATE transactions SET {sets} WHERE id = ?", [*updates.values(), tx_id])


def delete_transaction(conn, tx_id: int):
    conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))


def validate_transaction(conn, tx_type: str, amount_cents: int, from_id: Optional[int], to_id: Optional[int]):
    if amount_cents <= 0:
        raise ValueError("Amount must be positive")

    def acct_type(aid):
        row = conn.execute("SELECT account_type FROM accounts WHERE id = ? AND is_active = 1", (aid,)).fetchone()
        if not row:
            raise ValueError(f"Account id={aid} not found or inactive")
        return row[0]

    if tx_type == "EXPENSE":
        if not from_id:
            raise ValueError("Expense requires a source account")
        if to_id:
            raise ValueError("Expense must not have a destination account")
        acct_type(from_id)

    elif tx_type == "INCOME":
        if not to_id:
            raise ValueError("Income requires a destination account")
        if from_id:
            raise ValueError("Income must not have a source account")
        at = acct_type(to_id)
        if at == "credit_card":
            raise ValueError("Income cannot be received into a credit card account")

    elif tx_type == "TRANSFER":
        if not from_id or not to_id:
            raise ValueError("Transfer requires both source and destination accounts")
        if from_id == to_id:
            raise ValueError("Transfer source and destination must differ")
        acct_type(from_id)
        acct_type(to_id)
    else:
        raise ValueError(f"Unknown transaction type: {tx_type!r}")


def check_duplicates(conn, date: str, tx_type: str, amount_cents: int,
                     from_id: Optional[int], to_id: Optional[int]) -> list[int]:
    """Return IDs of existing transactions that look like duplicates."""
    conds = ["date = ?", "transaction_type = ?", "amount_cents = ?"]
    params = [date, tx_type, amount_cents]
    if from_id is not None:
        conds.append("from_account_id = ?"); params.append(from_id)
    if to_id is not None:
        conds.append("to_account_id = ?"); params.append(to_id)
    rows = conn.execute(
        "SELECT id FROM transactions WHERE " + " AND ".join(conds), params
    ).fetchall()
    return [r[0] for r in rows]


# ── Monthly Report Data ───────────────────────────────────────────────────────

def get_monthly_data(conn, year: int, month: int) -> dict:
    last_day = calendar.monthrange(year, month)[1]
    date_from = f"{year:04d}-{month:02d}-01"
    date_to = f"{year:04d}-{month:02d}-{last_day:02d}"

    txns = get_transactions(conn, date_from=date_from, date_to=date_to, limit=10_000)

    income_total = sum(t["amount_cents"] for t in txns if t["transaction_type"] == "INCOME")
    expense_total = sum(t["amount_cents"] for t in txns if t["transaction_type"] == "EXPENSE")
    transfer_total = sum(t["amount_cents"] for t in txns if t["transaction_type"] == "TRANSFER")

    income_by_cat: Dict[str, int] = {}
    expense_by_cat: Dict[str, int] = {}
    daily_spending: Dict[str, int] = {}
    spending_by_acct: Dict[str, int] = {}

    for t in txns:
        cat = t["category_name"] or "Uncategorized"
        if t["transaction_type"] == "INCOME":
            income_by_cat[cat] = income_by_cat.get(cat, 0) + t["amount_cents"]
        elif t["transaction_type"] == "EXPENSE":
            expense_by_cat[cat] = expense_by_cat.get(cat, 0) + t["amount_cents"]
            daily_spending[t["date"]] = daily_spending.get(t["date"], 0) + t["amount_cents"]
            acct = t["from_account_label"] or "Unknown"
            spending_by_acct[acct] = spending_by_acct.get(acct, 0) + t["amount_cents"]

    accounts = get_accounts(conn, as_of_date=date_to)

    return {
        "year": year,
        "month": month,
        "date_from": date_from,
        "date_to": date_to,
        "transactions": txns,
        "income_total": income_total,
        "expense_total": expense_total,
        "transfer_total": transfer_total,
        "net": income_total - expense_total,
        "income_by_cat": income_by_cat,
        "expense_by_cat": expense_by_cat,
        "daily_spending": daily_spending,
        "spending_by_acct": spending_by_acct,
        "accounts": accounts,
    }


# ── Settings ──────────────────────────────────────────────────────────────────

def get_settings(conn) -> Dict:
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    return {r["key"]: r["value"] for r in rows}


def update_setting(conn, key: str, value: str):
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
