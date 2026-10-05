"""Pydantic request/response models."""

from typing import Optional
from pydantic import BaseModel, field_validator


class AccountCreate(BaseModel):
    label: str
    account_type: str
    opening_balance_cents: int = 0
    opening_date: str = "2026-10-04"

    @field_validator("account_type")
    @classmethod
    def check_type(cls, v):
        if v not in ("bank", "cash", "credit_card"):
            raise ValueError("account_type must be bank, cash, or credit_card")
        return v

    @field_validator("opening_balance_cents")
    @classmethod
    def non_negative(cls, v):
        if v < 0:
            raise ValueError("opening_balance_cents cannot be negative")
        return v


class AccountUpdate(BaseModel):
    label: Optional[str] = None
    account_type: Optional[str] = None
    opening_balance_cents: Optional[int] = None
    opening_date: Optional[str] = None
    is_active: Optional[int] = None


class CategoryCreate(BaseModel):
    name: str
    transaction_type: str

    @field_validator("transaction_type")
    @classmethod
    def check_type(cls, v):
        if v not in ("expense", "income"):
            raise ValueError("transaction_type must be expense or income")
        return v


class CategoryUpdate(BaseModel):
    name: str


class TransactionCreate(BaseModel):
    date: str
    transaction_type: str
    amount_cents: int
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    category_id: Optional[int] = None
    description: str = ""

    @field_validator("transaction_type")
    @classmethod
    def check_type(cls, v):
        if v not in ("EXPENSE", "INCOME", "TRANSFER"):
            raise ValueError("transaction_type must be EXPENSE, INCOME, or TRANSFER")
        return v

    @field_validator("amount_cents")
    @classmethod
    def positive(cls, v):
        if v <= 0:
            raise ValueError("amount_cents must be positive")
        return v


class TransactionUpdate(BaseModel):
    date: Optional[str] = None
    transaction_type: Optional[str] = None
    amount_cents: Optional[int] = None
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    category_id: Optional[int] = None
    description: Optional[str] = None


class BatchPreviewRequest(BaseModel):
    text: str


class SettingsUpdate(BaseModel):
    tracking_start_date: Optional[str] = None
    app_title: Optional[str] = None


class ChangePinRequest(BaseModel):
    current_pin: str
    new_pin: str
    confirm_pin: str
