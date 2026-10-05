"""Batch transaction log parser for Expense Monitor.

Format (pipe-delimited):
    DATE | TYPE | AMOUNT | FROM_ACCOUNT | TO_ACCOUNT | CATEGORY | DESCRIPTION

Use '-' for fields that do not apply. Entries are separated by ';' or newlines.
"""

from dataclasses import dataclass
from datetime import date as Date
from typing import Optional
import re


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


@dataclass
class ParseError:
    raw: str
    line_number: int
    message: str


def _parse_amount(s: str) -> Optional[int]:
    """Return amount in cents, or None on invalid/negative input."""
    s = s.strip().replace(",", ".")
    try:
        val = float(s)
    except ValueError:
        return None
    if val < 0:
        return None
    return round(val * 100)


def _parse_date(s: str, today: str) -> Optional[str]:
    """Return ISO date string, today's date for '-'/empty, or None on invalid."""
    s = s.strip()
    if not s or s == "-":
        return today
    try:
        parts = s.split("-")
        if len(parts) != 3:
            return None
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        Date(y, m, d)
        return s
    except (ValueError, TypeError):
        return None


def parse_batch(text: str, today: str) -> list:
    """Parse a batch of entries separated by ';' or newlines."""
    raw_lines = re.split(r"[;\n]", text)
    results = []

    for line_no, raw in enumerate(raw_lines, start=1):
        raw = raw.strip()
        if not raw:
            continue

        fields = [f.strip() for f in raw.split("|")]
        if len(fields) != 7:
            results.append(ParseError(
                raw=raw, line_number=line_no,
                message=f"Expected 7 fields (| separated), got {len(fields)}.",
            ))
            continue

        date_str, tx_type, amount_str, from_str, to_str, cat_str, desc_str = fields

        parsed_date = _parse_date(date_str, today)
        if parsed_date is None:
            results.append(ParseError(raw=raw, line_number=line_no,
                                      message=f"Invalid date {date_str!r}. Use YYYY-MM-DD."))
            continue

        tx_type_upper = tx_type.strip().upper()
        if tx_type_upper not in ("EXPENSE", "INCOME", "TRANSFER"):
            results.append(ParseError(raw=raw, line_number=line_no,
                                      message=f"Invalid type {tx_type!r}. Use EXPENSE, INCOME, or TRANSFER."))
            continue

        amount_cents = _parse_amount(amount_str)
        if amount_cents is None:
            results.append(ParseError(raw=raw, line_number=line_no,
                                      message=f"Invalid amount {amount_str!r}. Use a positive number."))
            continue
        if amount_cents == 0:
            results.append(ParseError(raw=raw, line_number=line_no,
                                      message="Amount must be greater than zero."))
            continue

        from_account = None if (not from_str or from_str == "-") else from_str.upper()
        to_account = None if (not to_str or to_str == "-") else to_str.upper()
        category = None if (not cat_str or cat_str == "-") else cat_str
        description = "" if desc_str == "-" else desc_str

        if tx_type_upper == "EXPENSE":
            if not from_account:
                results.append(ParseError(raw=raw, line_number=line_no,
                                          message="EXPENSE requires FROM_ACCOUNT."))
                continue
            if to_account:
                results.append(ParseError(raw=raw, line_number=line_no,
                                          message="EXPENSE must not have a TO_ACCOUNT (use '-')."))
                continue

        elif tx_type_upper == "INCOME":
            if from_account:
                results.append(ParseError(raw=raw, line_number=line_no,
                                          message="INCOME must not have a FROM_ACCOUNT (use '-')."))
                continue
            if not to_account:
                results.append(ParseError(raw=raw, line_number=line_no,
                                          message="INCOME requires TO_ACCOUNT."))
                continue

        elif tx_type_upper == "TRANSFER":
            if not from_account or not to_account:
                results.append(ParseError(raw=raw, line_number=line_no,
                                          message="TRANSFER requires both FROM_ACCOUNT and TO_ACCOUNT."))
                continue
            if from_account == to_account:
                results.append(ParseError(raw=raw, line_number=line_no,
                                          message="TRANSFER FROM_ACCOUNT and TO_ACCOUNT must differ."))
                continue

        results.append(ParsedEntry(
            raw=raw,
            date=parsed_date,
            transaction_type=tx_type_upper,
            amount_cents=amount_cents,
            from_account=from_account,
            to_account=to_account,
            category=category,
            description=description,
        ))

    return results


def resolve_entry(entry: ParsedEntry, accounts_by_label: dict, cats_by_name: dict):
    """Resolve account/category names to IDs. Returns resolved dict or error string."""
    from_id = None
    to_id = None
    cat_id = None

    if entry.from_account:
        acc = accounts_by_label.get(entry.from_account.upper())
        if not acc:
            return f"Unknown account: {entry.from_account!r}"
        from_id = acc["id"]

    if entry.to_account:
        acc = accounts_by_label.get(entry.to_account.upper())
        if not acc:
            return f"Unknown account: {entry.to_account!r}"
        to_id = acc["id"]

    if entry.category:
        cat = cats_by_name.get(entry.category)
        if cat is None:
            cat = next(
                (c for name, c in cats_by_name.items() if name.lower() == entry.category.lower()),
                None,
            )
        if cat:
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
