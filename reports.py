"""Chart generation using matplotlib (offline, server-side)."""

from __future__ import annotations

import io
import calendar
from typing import Dict
import matplotlib
matplotlib.use("Agg")  # non-interactive backend — must be before pyplot import
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

PALETTE = ["#2563eb", "#16a34a", "#dc2626", "#ea580c", "#7c3aed",
           "#0891b2", "#d97706", "#be123c", "#15803d", "#1d4ed8"]


def _cents_to_eur(cents: int) -> float:
    return cents / 100


def _render_png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    buf.seek(0)
    data = buf.read()
    plt.close(fig)
    return data


def chart_expense_by_category(expense_by_cat: Dict[str, int]) -> bytes:
    """Horizontal bar chart of spending by category."""
    if not expense_by_cat:
        return _empty_chart("No expenses this month")

    sorted_items = sorted(expense_by_cat.items(), key=lambda x: x[1])
    labels = [k for k, _ in sorted_items]
    values = [_cents_to_eur(v) for _, v in sorted_items]

    fig, ax = plt.subplots(figsize=(8, max(3, len(labels) * 0.5 + 1)))
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(labels))]
    bars = ax.barh(labels, values, color=colors, height=0.6)
    ax.bar_label(bars, labels=[f"€{v:,.2f}" for v in values], padding=4, fontsize=9)
    ax.set_xlabel("Amount (EUR)")
    ax.set_title("Expenses by Category", fontsize=12, fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:,.0f}"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _render_png(fig)


def chart_daily_spending(daily_spending: Dict[str, int], year: int, month: int) -> bytes:
    """Bar chart of daily spending over the month."""
    last_day = calendar.monthrange(year, month)[1]
    all_days = [f"{year:04d}-{month:02d}-{d:02d}" for d in range(1, last_day + 1)]
    values = [_cents_to_eur(daily_spending.get(d, 0)) for d in all_days]
    day_labels = [str(d) for d in range(1, last_day + 1)]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(day_labels, values, color=PALETTE[0], width=0.7)
    ax.set_xlabel("Day of Month")
    ax.set_ylabel("Amount (EUR)")
    ax.set_title(f"Daily Spending — {calendar.month_name[month]} {year}", fontsize=12, fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:,.0f}"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    # Only show every 5th x-label to avoid crowding
    for i, label in enumerate(ax.xaxis.get_ticklabels()):
        if (i + 1) % 5 != 0 and i != 0:
            label.set_visible(False)
    fig.tight_layout()
    return _render_png(fig)


def chart_income_vs_expenses(income_total: int, expense_total: int) -> bytes:
    """Grouped bar chart comparing income and expenses."""
    categories = ["Income", "Expenses", "Net"]
    net = income_total - expense_total
    values = [
        _cents_to_eur(income_total),
        _cents_to_eur(expense_total),
        _cents_to_eur(abs(net)),
    ]
    colors = [
        PALETTE[1],   # green for income
        PALETTE[2],   # red for expenses
        PALETTE[0] if net >= 0 else PALETTE[2],  # blue if surplus, red if deficit
    ]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(categories, values, color=colors, width=0.5)
    ax.bar_label(bars, labels=[f"€{v:,.2f}" for v in values], padding=4, fontsize=10)
    ax.set_ylabel("Amount (EUR)")
    title_suffix = "Surplus" if net >= 0 else "Deficit"
    ax.set_title(f"Income vs Expenses  ({title_suffix}: €{_cents_to_eur(abs(net)):,.2f})", fontsize=11, fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:,.0f}"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _render_png(fig)


def chart_spending_by_account(spending_by_acct: Dict[str, int]) -> bytes:
    """Bar chart of spending per payment method / account."""
    if not spending_by_acct:
        return _empty_chart("No expense data")

    sorted_items = sorted(spending_by_acct.items(), key=lambda x: x[1], reverse=True)
    labels = [k for k, _ in sorted_items]
    values = [_cents_to_eur(v) for _, v in sorted_items]

    fig, ax = plt.subplots(figsize=(6, 4))
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(labels))]
    bars = ax.bar(labels, values, color=colors, width=0.5)
    ax.bar_label(bars, labels=[f"€{v:,.2f}" for v in values], padding=4, fontsize=9)
    ax.set_ylabel("Amount (EUR)")
    ax.set_title("Spending by Payment Method", fontsize=12, fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:,.0f}"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _render_png(fig)


def _empty_chart(message: str) -> bytes:
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=12, color="#64748b", transform=ax.transAxes)
    ax.axis("off")
    return _render_png(fig)
