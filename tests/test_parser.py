"""Tests for the batch transaction log parser."""

import pytest
from tx_parser import parse_batch, ParsedEntry, ParseError, _parse_amount, _parse_date, resolve_entry


TODAY = "2026-10-04"

# ── Amount Parsing ─────────────────────────────────────────────────────────────

def test_parse_amount_decimal_dot():
    assert _parse_amount("18.70") == 1870

def test_parse_amount_decimal_comma():
    assert _parse_amount("18,70") == 1870

def test_parse_amount_integer():
    assert _parse_amount("3200") == 320000

def test_parse_amount_zero():
    assert _parse_amount("0") == 0

def test_parse_amount_negative():
    assert _parse_amount("-5.00") is None

def test_parse_amount_invalid():
    assert _parse_amount("abc") is None

def test_parse_amount_whitespace():
    assert _parse_amount("  42.00  ") == 4200


# ── Date Parsing ───────────────────────────────────────────────────────────────

def test_parse_date_valid():
    assert _parse_date("2026-10-04", TODAY) == "2026-10-04"

def test_parse_date_dash_uses_today():
    assert _parse_date("-", TODAY) == TODAY

def test_parse_date_empty_uses_today():
    assert _parse_date("", TODAY) == TODAY

def test_parse_date_invalid_format():
    assert _parse_date("04.10.2026", TODAY) is None

def test_parse_date_invalid_calendar():
    assert _parse_date("2026-13-01", TODAY) is None


# ── Full Line Parsing ──────────────────────────────────────────────────────────

def test_parse_expense_valid():
    text = "2026-10-04 | EXPENSE | 18.70 | CARD | - | Eating out | Lunch"
    results = parse_batch(text, TODAY)
    assert len(results) == 1
    entry = results[0]
    assert isinstance(entry, ParsedEntry)
    assert entry.transaction_type == "EXPENSE"
    assert entry.amount_cents == 1870
    assert entry.from_account == "CARD"
    assert entry.to_account is None
    assert entry.category == "Eating out"
    assert entry.description == "Lunch"


def test_parse_income_valid():
    text = "2026-10-04 | INCOME | 3200.00 | - | BANK-1 | Salary | October salary"
    results = parse_batch(text, TODAY)
    assert len(results) == 1
    entry = results[0]
    assert isinstance(entry, ParsedEntry)
    assert entry.transaction_type == "INCOME"
    assert entry.amount_cents == 320000
    assert entry.from_account is None
    assert entry.to_account == "BANK-1"


def test_parse_transfer_valid():
    text = "2026-10-04 | TRANSFER | 50.00 | BANK-1 | CASH | - | ATM withdrawal"
    results = parse_batch(text, TODAY)
    assert len(results) == 1
    entry = results[0]
    assert isinstance(entry, ParsedEntry)
    assert entry.transaction_type == "TRANSFER"
    assert entry.from_account == "BANK-1"
    assert entry.to_account == "CASH"
    assert entry.category is None


def test_parse_batch_semicolon_separator():
    text = ("2026-10-04 | EXPENSE | 10.00 | CARD | - | Eating out | Coffee;"
            "2026-10-04 | INCOME | 500.00 | - | BANK-1 | Bonus | Q3 bonus")
    results = parse_batch(text, TODAY)
    assert len(results) == 2
    assert isinstance(results[0], ParsedEntry)
    assert isinstance(results[1], ParsedEntry)


def test_parse_batch_newline_separator():
    text = "2026-10-04 | EXPENSE | 10.00 | CARD | - | Eating out | Coffee\n2026-10-04 | INCOME | 500.00 | - | BANK-1 | Bonus | Q3"
    results = parse_batch(text, TODAY)
    assert len(results) == 2


def test_parse_missing_field_count():
    text = "2026-10-04 | EXPENSE | 18.70 | CARD | - | Eating out"
    results = parse_batch(text, TODAY)
    assert len(results) == 1
    assert isinstance(results[0], ParseError)
    assert "7" in results[0].message


def test_parse_invalid_type():
    text = "2026-10-04 | BUY | 18.70 | CARD | - | Eating out | Lunch"
    results = parse_batch(text, TODAY)
    assert isinstance(results[0], ParseError)


def test_parse_zero_amount_error():
    text = "2026-10-04 | EXPENSE | 0 | CARD | - | Eating out | Free"
    results = parse_batch(text, TODAY)
    assert isinstance(results[0], ParseError)


def test_parse_expense_with_to_account_error():
    text = "2026-10-04 | EXPENSE | 18.70 | CARD | BANK-1 | Eating out | Lunch"
    results = parse_batch(text, TODAY)
    assert isinstance(results[0], ParseError)
    assert "TO_ACCOUNT" in results[0].message


def test_parse_income_with_from_account_error():
    text = "2026-10-04 | INCOME | 100.00 | BANK-1 | BANK-2 | Salary | Wages"
    results = parse_batch(text, TODAY)
    assert isinstance(results[0], ParseError)


def test_parse_transfer_missing_to_account():
    text = "2026-10-04 | TRANSFER | 50.00 | BANK-1 | - | - | ATM"
    results = parse_batch(text, TODAY)
    assert isinstance(results[0], ParseError)
    assert "both" in results[0].message.lower()


def test_parse_transfer_same_account_error():
    text = "2026-10-04 | TRANSFER | 50.00 | BANK-1 | BANK-1 | - | Self"
    results = parse_batch(text, TODAY)
    assert isinstance(results[0], ParseError)


def test_parse_empty_lines_skipped():
    text = "2026-10-04 | EXPENSE | 10.00 | CARD | - | Eating out | Coffee\n\n\n"
    results = parse_batch(text, TODAY)
    assert len(results) == 1


def test_parse_german_decimal_comma():
    text = "2026-10-04 | EXPENSE | 18,70 | CARD | - | Eating out | Lunch"
    results = parse_batch(text, TODAY)
    assert isinstance(results[0], ParsedEntry)
    assert results[0].amount_cents == 1870


def test_parse_type_case_insensitive():
    text = "2026-10-04 | expense | 18.70 | CARD | - | Eating out | Lunch"
    results = parse_batch(text, TODAY)
    assert isinstance(results[0], ParsedEntry)
    assert results[0].transaction_type == "EXPENSE"


# ── Resolve Entry ─────────────────────────────────────────────────────────────

def test_resolve_unknown_account():
    from tx_parser import ParsedEntry
    entry = ParsedEntry(
        raw="", date=TODAY, transaction_type="EXPENSE",
        amount_cents=1000, from_account="UNKNOWN-BANK",
        to_account=None, category=None, description=""
    )
    accounts = {"BANK-1": {"id": 1}}
    cats = {}
    result = resolve_entry(entry, accounts, cats)
    assert isinstance(result, str)
    assert "UNKNOWN-BANK" in result


def test_resolve_success():
    from tx_parser import ParsedEntry
    entry = ParsedEntry(
        raw="", date=TODAY, transaction_type="EXPENSE",
        amount_cents=1870, from_account="CARD",
        to_account=None, category="Eating out", description="Lunch"
    )
    accounts = {"CARD": {"id": 5}}
    cats = {"Eating out": {"id": 2}}
    result = resolve_entry(entry, accounts, cats)
    assert isinstance(result, dict)
    assert result["from_account_id"] == 5
    assert result["category_id"] == 2
