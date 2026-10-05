"""Phone-log batch parser.

Format (pipe-delimited, entries separated by ';' or newlines):
  DATE | TYPE | AMOUNT | FROM_ACCOUNT | TO_ACCOUNT | CATEGORY | DESCRIPTION

Use '-' for fields that do not apply.
Amounts are positive decimals; use '.' or ',' as decimal separator.

Examples:
  2026-10-04 | EXPENSE  | 18.70  | CARD   | -      | Eating out | Lunch
  2026-10-04 | INCOME   | 3200   | -      | BANK-1 | Salary     | October salary
  2026-10-04 | TRANSFER | 200.00 | BANK-1 | BANK-2 | -          | Savings
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date as Date
from typing import Dict, List, Optional, Union


@dataclass
class ParsedEntry:
    raw: str
    date: str
    transaction_type: str
    amount_cents: int
    from_account: Optional[str]
    to_account: Optional[str]
    category: Optional[str]
    description: str
    duplicate_ids: list[int] = field(default_factory=list)


@dataclass
class ParseError:
    raw: str
    line_number: int
    message: str


def parse_batch(text: str, today: Optional[str] = None) -> list[ParsedEntry | ParseError]:
    """Split and parse a pasted batch of transaction lines."""
    if today is None:
        today = Date.today().isoformat()

    # Split on ';' or newlines; handle both
    raw_lines = re.split(r";|\n", text)
    results: list[ParsedEntry | ParseError] = []
    line_no = 0

    for raw in raw_lines:
        raw = raw.strip()
        if not raw:
            continue
        line_no += 1
        result = _parse_line(raw, line_no, today)
        results.append(result)

    return results


def _parse_line(raw: str, line_no: int, today: str) -> ParsedEntry | ParseError:
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) != 7:
        return ParseError(raw, line_no, f"Expected 7 pipe-separated fields, got {len(parts)}")

    date_s, type_s, amount_s, from_s, to_s, cat_s, desc_s = parts

    # Date
    date_val = _parse_date(date_s, today)
    if date_val is None:
        return ParseError(raw, line_no, f"Invalid date {date_s!r}. Use YYYY-MM-DD or '-' for today.")

    # Type
    tx_type = type_s.strip().upper()
    if tx_type not in ("EXPENSE", "INCOME", "TRANSFER"):
        return ParseError(raw, line_no, f"Unknown type {type_s!r}. Use EXPENSE, INCOME, or TRANSFER.")

    # Amount
    amount_cents = _parse_amount(amount_s)
    if amount_cents is None:
        return ParseError(raw, line_no, f"Invalid amount {amount_s!r}. Use a positive decimal like '18.70'.")
    if amount_cents <= 0:
        return ParseError(raw, line_no, "Amount must be greater than zero.")

    # Accounts
    from_acc = None if from_s in ("-", "") else from_s.strip().upper()
    to_acc = None if to_s in ("-", "") else to_s.strip().upper()

    # Category
    category = None if cat_s in ("-", "") else cat_s.strip()

    # Description
    description = desc_s.strip()

    # Structural validation
    error = _structural_check(tx_type, from_acc, to_acc)
    if error:
        return ParseError(raw, line_no, error)

    return ParsedEntry(
        raw=raw,
        date=date_val,
        transaction_type=tx_type,
        amount_cents=amount_cents,
        from_account=from_acc,
        to_account=to_acc,
        category=category,
        description=description,
    )


def _parse_date(s: str, today: str) -> Optional[str]:
    s = s.strip()
    if s in ("-", ""):
        return today
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        try:
            year, month, day = map(int, s.split("-"))
            Date(year, month, day)
            return s
        except ValueError:
            return None
    return None


def _parse_amount(s: str) -> Optional[int]:
    """Parse a decimal string to integer cents. Accepts '.' or ',' as decimal separator."""
    s = s.strip().replace(",", ".")
    try:
        value = float(s)
        if value < 0:
            return None
        return round(value * 100)
    except ValueError:
        return None


def _structural_check(tx_type: str, from_acc: Optional[str], to_acc: Optional[str]) -> Optional[str]:
    if tx_type == "EXPENSE":
        if not from_acc:
            return "EXPENSE requires FROM_ACCOUNT (the paying account). Use '-' only in TO_ACCOUNT."
        if to_acc:
            return "EXPENSE must have '-' in TO_ACCOUNT."
    elif tx_type == "INCOME":
        if not to_acc:
            return "INCOME requires TO_ACCOUNT (the receiving account). Use '-' only in FROM_ACCOUNT."
        if from_acc:
            return "INCOME must have '-' in FROM_ACCOUNT."
    elif tx_type == "TRANSFER":
        if not from_acc or not to_acc:
            return "TRANSFER requires both FROM_ACCOUNT and TO_ACCOUNT."
        if from_acc == to_acc:
            return "TRANSFER FROM_ACCOUNT and TO_ACCOUNT must be different."
    return None


def resolve_entry(entry: ParsedEntry, accounts_by_label: dict, categories_by_name: dict) -> dict | str:
    """
    Map account labels and category names to IDs.
    Returns a dict ready for create_transaction() or an error string.
    """
    from_id = None
    to_id = None
    cat_id = None

    if entry.from_account:
        acc = accounts_by_label.get(entry.from_account.upper())
        if acc is None:
            return f"Account '{entry.from_account}' not found. Known accounts: {', '.join(accounts_by_label)}"
        from_id = acc["id"]

    if entry.to_account:
        acc = accounts_by_label.get(entry.to_account.upper())
        if acc is None:
            return f"Account '{entry.to_account}' not found. Known accounts: {', '.join(accounts_by_label)}"
        to_id = acc["id"]

    if entry.category:
        key = entry.category.lower()
        # Try exact match first, then case-insensitive
        cat = categories_by_name.get(entry.category) or categories_by_name.get(key)
        if cat is None:
            # Fuzzy: check all
            for k, v in categories_by_name.items():
                if k.lower() == key:
                    cat = v
                    break
        if cat is None:
            return f"Category '{entry.category}' not found."
        cat_id = cat["id"]

    return {
        "date": entry.date,
        "transaction_type": entry.transaction_type,
        "amount_cents": entry.amount_cents,
        "from_account_id": from_id,
        "to_account_id": to_id,
        "category_id": cat_id,
        "description": entry.description,
    }
