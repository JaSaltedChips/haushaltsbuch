"""Tests for accounting rules and balance calculations."""

import pytest
import database as db


# ── Balance calculation ────────────────────────────────────────────────────────

def test_initial_balances_are_zero(conn, account_ids):
    accounts = db.get_accounts(conn)
    for acc in accounts:
        assert acc["balance_cents"] == 0, f"{acc['label']} should start at 0"


def test_opening_balance_reflected(conn, account_ids):
    db.update_account(conn, account_ids["BANK-1"], opening_balance_cents=500_00)
    conn.commit()
    acc = db.get_account(conn, account_ids["BANK-1"])
    assert acc["balance_cents"] == 500_00


def test_income_increases_bank_balance(conn, account_ids):
    cats = db.get_categories(conn, "income")
    cat_id = cats[0]["id"]
    db.create_transaction(conn, "2026-10-04", "INCOME", 3200_00,
                          to_account_id=account_ids["BANK-1"], category_id=cat_id)
    conn.commit()
    acc = db.get_account(conn, account_ids["BANK-1"])
    assert acc["balance_cents"] == 3200_00


def test_expense_from_bank_decreases_balance(conn, account_ids):
    db.update_account(conn, account_ids["BANK-1"], opening_balance_cents=1000_00)
    cats = db.get_categories(conn, "expense")
    cat_id = cats[0]["id"]
    db.create_transaction(conn, "2026-10-04", "EXPENSE", 50_00,
                          from_account_id=account_ids["BANK-1"], category_id=cat_id)
    conn.commit()
    acc = db.get_account(conn, account_ids["BANK-1"])
    assert acc["balance_cents"] == 950_00


def test_expense_on_card_increases_owed(conn, account_ids):
    cats = db.get_categories(conn, "expense")
    cat_id = cats[0]["id"]
    db.create_transaction(conn, "2026-10-04", "EXPENSE", 18_70,
                          from_account_id=account_ids["CARD"], category_id=cat_id,
                          description="Lunch")
    conn.commit()
    acc = db.get_account(conn, account_ids["CARD"])
    assert acc["balance_cents"] == 18_70, "Card balance (amount owed) should increase"


def test_card_payment_reduces_owed_and_bank(conn, account_ids):
    cats = db.get_categories(conn, "expense")
    cat_id = cats[0]["id"]
    db.update_account(conn, account_ids["BANK-1"], opening_balance_cents=1000_00)
    # Charge card
    db.create_transaction(conn, "2026-10-04", "EXPENSE", 200_00,
                          from_account_id=account_ids["CARD"], category_id=cat_id)
    # Pay card from bank
    db.create_transaction(conn, "2026-10-05", "TRANSFER", 200_00,
                          from_account_id=account_ids["BANK-1"],
                          to_account_id=account_ids["CARD"])
    conn.commit()

    bank = db.get_account(conn, account_ids["BANK-1"])
    card = db.get_account(conn, account_ids["CARD"])
    assert card["balance_cents"] == 0, "Card balance should be 0 after full payment"
    assert bank["balance_cents"] == 800_00, "Bank should decrease by card payment amount"


def test_card_payment_not_counted_as_expense(conn, account_ids):
    """A transfer to CARD (payment) must NOT appear as an expense in reports."""
    db.update_account(conn, account_ids["BANK-1"], opening_balance_cents=1000_00)
    db.create_transaction(conn, "2026-10-05", "TRANSFER", 150_00,
                          from_account_id=account_ids["BANK-1"],
                          to_account_id=account_ids["CARD"])
    conn.commit()
    data = db.get_monthly_data(conn, 2026, 10)
    assert data["expense_total"] == 0, "Card payment (transfer) must not be counted as expense"
    assert data["transfer_total"] == 150_00


def test_cash_withdrawal_is_transfer_not_expense(conn, account_ids):
    db.update_account(conn, account_ids["BANK-1"], opening_balance_cents=500_00)
    db.create_transaction(conn, "2026-10-04", "TRANSFER", 50_00,
                          from_account_id=account_ids["BANK-1"],
                          to_account_id=account_ids["CASH"])
    conn.commit()
    data = db.get_monthly_data(conn, 2026, 10)
    assert data["expense_total"] == 0
    assert data["income_total"] == 0
    assert data["transfer_total"] == 50_00

    bank = db.get_account(conn, account_ids["BANK-1"])
    cash = db.get_account(conn, account_ids["CASH"])
    assert bank["balance_cents"] == 450_00
    assert cash["balance_cents"] == 50_00


def test_inter_bank_transfer_not_income_or_expense(conn, account_ids):
    db.update_account(conn, account_ids["BANK-1"], opening_balance_cents=1000_00)
    db.create_transaction(conn, "2026-10-04", "TRANSFER", 200_00,
                          from_account_id=account_ids["BANK-1"],
                          to_account_id=account_ids["BANK-2"])
    conn.commit()
    data = db.get_monthly_data(conn, 2026, 10)
    assert data["income_total"] == 0
    assert data["expense_total"] == 0
    bank1 = db.get_account(conn, account_ids["BANK-1"])
    bank2 = db.get_account(conn, account_ids["BANK-2"])
    assert bank1["balance_cents"] == 800_00
    assert bank2["balance_cents"] == 200_00


def test_card_purchase_counted_once_as_expense(conn, account_ids):
    """A card purchase must be counted exactly once as an expense, not again when paid."""
    cats = db.get_categories(conn, "expense")
    cat_id = cats[0]["id"]
    db.update_account(conn, account_ids["BANK-1"], opening_balance_cents=1000_00)

    # Card purchase
    db.create_transaction(conn, "2026-10-04", "EXPENSE", 100_00,
                          from_account_id=account_ids["CARD"], category_id=cat_id,
                          description="Groceries")
    # Card payment
    db.create_transaction(conn, "2026-10-05", "TRANSFER", 100_00,
                          from_account_id=account_ids["BANK-1"],
                          to_account_id=account_ids["CARD"])
    conn.commit()

    data = db.get_monthly_data(conn, 2026, 10)
    assert data["expense_total"] == 100_00, "Expense counted once"
    assert data["transfer_total"] == 100_00, "Payment is a transfer"


def test_negative_balance_possible_for_bank(conn, account_ids):
    cats = db.get_categories(conn, "expense")
    cat_id = cats[0]["id"]
    db.create_transaction(conn, "2026-10-04", "EXPENSE", 50_00,
                          from_account_id=account_ids["BANK-1"], category_id=cat_id)
    conn.commit()
    acc = db.get_account(conn, account_ids["BANK-1"])
    assert acc["balance_cents"] == -50_00


def test_balance_as_of_date(conn, account_ids):
    cats = db.get_categories(conn, "income")
    cat_id = cats[0]["id"]
    db.create_transaction(conn, "2026-10-01", "INCOME", 1000_00,
                          to_account_id=account_ids["BANK-1"], category_id=cat_id)
    db.create_transaction(conn, "2026-10-15", "INCOME", 500_00,
                          to_account_id=account_ids["BANK-1"], category_id=cat_id)
    conn.commit()
    accounts_oct10 = db.get_accounts(conn, as_of_date="2026-10-10")
    bank = next(a for a in accounts_oct10 if a["label"] == "BANK-1")
    assert bank["balance_cents"] == 1000_00, "Only first income before Oct 10"


# ── Validation ────────────────────────────────────────────────────────────────

def test_expense_requires_from_account(conn, account_ids):
    with pytest.raises(ValueError, match="source account"):
        db.validate_transaction(conn, "EXPENSE", 100_00, None, None)


def test_income_cannot_go_to_credit_card(conn, account_ids):
    with pytest.raises(ValueError, match="credit card"):
        db.validate_transaction(conn, "INCOME", 100_00, None, account_ids["CARD"])


def test_transfer_requires_both_accounts(conn, account_ids):
    with pytest.raises(ValueError, match="both"):
        db.validate_transaction(conn, "TRANSFER", 100_00, account_ids["BANK-1"], None)


def test_transfer_same_account_rejected(conn, account_ids):
    with pytest.raises(ValueError, match="differ"):
        db.validate_transaction(conn, "TRANSFER", 100_00, account_ids["BANK-1"], account_ids["BANK-1"])


def test_zero_amount_rejected(conn, account_ids):
    with pytest.raises(ValueError, match="positive"):
        db.validate_transaction(conn, "EXPENSE", 0, account_ids["BANK-1"], None)


def test_income_must_not_have_from_account(conn, account_ids):
    with pytest.raises(ValueError, match="source account"):
        db.validate_transaction(conn, "INCOME", 100_00, account_ids["BANK-1"], account_ids["BANK-2"])


# ── Duplicate Detection ───────────────────────────────────────────────────────

def test_duplicate_detection(conn, account_ids):
    cats = db.get_categories(conn, "expense")
    cat_id = cats[0]["id"]
    db.create_transaction(conn, "2026-10-04", "EXPENSE", 18_70,
                          from_account_id=account_ids["CARD"], category_id=cat_id)
    conn.commit()
    dups = db.check_duplicates(conn, "2026-10-04", "EXPENSE", 18_70,
                               account_ids["CARD"], None)
    assert len(dups) == 1


def test_no_false_positive_duplicate(conn, account_ids):
    cats = db.get_categories(conn, "expense")
    cat_id = cats[0]["id"]
    db.create_transaction(conn, "2026-10-04", "EXPENSE", 18_70,
                          from_account_id=account_ids["CARD"], category_id=cat_id)
    conn.commit()
    # Different date → not a duplicate
    dups = db.check_duplicates(conn, "2026-10-05", "EXPENSE", 18_70,
                               account_ids["CARD"], None)
    assert len(dups) == 0
