"""Tests for monthly report data calculations."""

import pytest
import database as db


def setup_sample_month(conn, account_ids):
    """Insert a representative October 2026 dataset."""
    exp_cats = {c["name"]: c["id"] for c in db.get_categories(conn, "expense")}
    inc_cats = {c["name"]: c["id"] for c in db.get_categories(conn, "income")}

    db.update_account(conn, account_ids["BANK-1"], opening_balance_cents=2000_00)

    # Salary → BANK-1
    db.create_transaction(conn, "2026-10-01", "INCOME", 3200_00,
                          to_account_id=account_ids["BANK-1"],
                          category_id=inc_cats["Salary"],
                          description="October salary")
    # Card expense — groceries
    db.create_transaction(conn, "2026-10-03", "EXPENSE", 85_50,
                          from_account_id=account_ids["CARD"],
                          category_id=exp_cats["Groceries"],
                          description="Supermarket")
    # Card expense — eating out
    db.create_transaction(conn, "2026-10-04", "EXPENSE", 18_70,
                          from_account_id=account_ids["CARD"],
                          category_id=exp_cats["Eating out"],
                          description="Lunch")
    # Direct bank expense
    db.create_transaction(conn, "2026-10-05", "EXPENSE", 120_00,
                          from_account_id=account_ids["BANK-1"],
                          category_id=exp_cats["Housing and bills"],
                          description="Electricity bill")
    # Cash ATM withdrawal (TRANSFER)
    db.create_transaction(conn, "2026-10-06", "TRANSFER", 50_00,
                          from_account_id=account_ids["BANK-1"],
                          to_account_id=account_ids["CASH"])
    # Card payment (TRANSFER, should NOT be an expense)
    db.create_transaction(conn, "2026-10-10", "TRANSFER", 104_20,
                          from_account_id=account_ids["BANK-1"],
                          to_account_id=account_ids["CARD"])
    conn.commit()


def test_income_total(conn, account_ids):
    setup_sample_month(conn, account_ids)
    data = db.get_monthly_data(conn, 2026, 10)
    assert data["income_total"] == 3200_00


def test_expense_total_excludes_transfers(conn, account_ids):
    setup_sample_month(conn, account_ids)
    data = db.get_monthly_data(conn, 2026, 10)
    expected = 85_50 + 18_70 + 120_00
    assert data["expense_total"] == expected, f"Expected {expected}, got {data['expense_total']}"


def test_transfer_total(conn, account_ids):
    setup_sample_month(conn, account_ids)
    data = db.get_monthly_data(conn, 2026, 10)
    expected_transfers = 50_00 + 104_20
    assert data["transfer_total"] == expected_transfers


def test_net_income(conn, account_ids):
    setup_sample_month(conn, account_ids)
    data = db.get_monthly_data(conn, 2026, 10)
    assert data["net"] == data["income_total"] - data["expense_total"]


def test_expense_by_category(conn, account_ids):
    setup_sample_month(conn, account_ids)
    data = db.get_monthly_data(conn, 2026, 10)
    cats = data["expense_by_cat"]
    assert cats.get("Groceries") == 85_50
    assert cats.get("Eating out") == 18_70
    assert cats.get("Housing and bills") == 120_00


def test_income_by_category(conn, account_ids):
    setup_sample_month(conn, account_ids)
    data = db.get_monthly_data(conn, 2026, 10)
    assert data["income_by_cat"].get("Salary") == 3200_00


def test_daily_spending_only_expenses(conn, account_ids):
    setup_sample_month(conn, account_ids)
    data = db.get_monthly_data(conn, 2026, 10)
    # Transfers should not appear in daily_spending
    assert "2026-10-06" not in data["daily_spending"]  # ATM withdrawal is a transfer
    assert data["daily_spending"].get("2026-10-03") == 85_50
    assert data["daily_spending"].get("2026-10-04") == 18_70
    assert data["daily_spending"].get("2026-10-05") == 120_00


def test_spending_by_account(conn, account_ids):
    setup_sample_month(conn, account_ids)
    data = db.get_monthly_data(conn, 2026, 10)
    accts = data["spending_by_acct"]
    assert accts.get("CARD") == 85_50 + 18_70
    assert accts.get("BANK-1") == 120_00


def test_account_balances_end_of_month(conn, account_ids):
    setup_sample_month(conn, account_ids)
    data = db.get_monthly_data(conn, 2026, 10)
    balances = {a["label"]: a["balance_cents"] for a in data["accounts"]}

    # BANK-1: 2000 (opening) + 3200 (salary) - 120 (electric) - 50 (ATM) - 104.20 (card payment)
    expected_bank1 = 2000_00 + 3200_00 - 120_00 - 50_00 - 104_20
    assert balances["BANK-1"] == expected_bank1

    # CASH: 0 + 50 (ATM) = 50
    assert balances["CASH"] == 50_00

    # CARD: 0 (opening) + 85.50 + 18.70 (expenses) - 104.20 (payment) = 0
    assert balances["CARD"] == 0


def test_empty_month_returns_zero_totals(conn, account_ids):
    data = db.get_monthly_data(conn, 2025, 1)
    assert data["income_total"] == 0
    assert data["expense_total"] == 0
    assert data["transfer_total"] == 0
    assert data["net"] == 0


def test_transactions_in_different_month_excluded(conn, account_ids):
    inc_cats = {c["name"]: c["id"] for c in db.get_categories(conn, "income")}
    db.create_transaction(conn, "2026-09-30", "INCOME", 1000_00,
                          to_account_id=account_ids["BANK-1"],
                          category_id=inc_cats["Salary"])
    conn.commit()
    data = db.get_monthly_data(conn, 2026, 10)
    assert data["income_total"] == 0, "September income must not appear in October report"


def test_multiple_expenses_same_category(conn, account_ids):
    exp_cats = {c["name"]: c["id"] for c in db.get_categories(conn, "expense")}
    db.create_transaction(conn, "2026-10-01", "EXPENSE", 30_00,
                          from_account_id=account_ids["CASH"],
                          category_id=exp_cats["Groceries"])
    db.create_transaction(conn, "2026-10-03", "EXPENSE", 45_00,
                          from_account_id=account_ids["CASH"],
                          category_id=exp_cats["Groceries"])
    conn.commit()
    data = db.get_monthly_data(conn, 2026, 10)
    assert data["expense_by_cat"]["Groceries"] == 75_00
