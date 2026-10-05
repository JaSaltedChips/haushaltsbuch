"""Expense Monitor — FastAPI application entry point."""

import csv
import io
from datetime import date as Date
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse as _JSONResponse

import auth
import database as db
import reports
from models import (
    AccountCreate, AccountUpdate,
    BatchPreviewRequest,
    CategoryCreate, CategoryUpdate,
    ChangePinRequest,
    SettingsUpdate,
    TransactionCreate, TransactionUpdate,
)
from tx_parser import parse_batch, resolve_entry, ParseError

BASE_DIR = Path(__file__).parent

app = FastAPI(title="Expense Monitor", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# ── Auth middleware ────────────────────────────────────────────────────────────

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path == "/login" or path.startswith("/static"):
            return await call_next(request)
        token = request.cookies.get(auth.SESSION_COOKIE)
        if not auth.is_valid_session(token):
            if path.startswith("/api/"):
                return _JSONResponse({"detail": "Not authenticated"}, status_code=401)
            return RedirectResponse("/login", status_code=303)
        return await call_next(request)

app.add_middleware(AuthMiddleware)


@app.on_event("startup")
def startup():
    db.init_db()


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
async def page_login(request: Request):
    with db.get_connection() as conn:
        settings = db.get_settings(conn)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "pin_set": bool(settings.get("pin_hash")),
        "error": "",
        "session_hours": auth.SESSION_HOURS,
    })


@app.post("/login")
async def do_login(request: Request, pin: str = Form(...)):
    locked, secs = auth.check_lockout()
    if locked:
        return templates.TemplateResponse("login.html", {
            "request": request, "pin_set": True, "session_hours": auth.SESSION_HOURS,
            "error": f"Too many wrong attempts. Try again in {secs} second(s).",
        }, status_code=429)

    with db.get_connection() as conn:
        settings = db.get_settings(conn)
    pin_hash = settings.get("pin_hash", "")

    # ── First run: no PIN set yet — treat POST as PIN setup ──────────────────
    if not pin_hash:
        if len(pin) < 4:
            return templates.TemplateResponse("login.html", {
                "request": request, "pin_set": False, "session_hours": auth.SESSION_HOURS,
                "error": "PIN must be at least 4 characters.",
            }, status_code=400)
        with db.get_connection() as conn:
            db.update_setting(conn, "pin_hash", auth.hash_pin(pin))
        token = auth.create_session()
        resp = RedirectResponse("/", status_code=303)
        resp.set_cookie(auth.SESSION_COOKIE, token, httponly=True,
                        samesite="strict", max_age=auth.SESSION_HOURS * 3600)
        return resp

    # ── Normal login ─────────────────────────────────────────────────────────
    if not auth.verify_pin(pin, pin_hash):
        auth.record_failure()
        locked, secs = auth.check_lockout()
        error = (f"Wrong PIN — too many attempts, wait {secs}s." if locked
                 else "Wrong PIN. Please try again.")
        return templates.TemplateResponse("login.html", {
            "request": request, "pin_set": True, "session_hours": auth.SESSION_HOURS,
            "error": error,
        }, status_code=401)

    auth.record_success()
    token = auth.create_session()
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie(auth.SESSION_COOKIE, token, httponly=True,
                    samesite="strict", max_age=auth.SESSION_HOURS * 3600)
    return resp


@app.get("/logout")
async def do_logout(request: Request):
    token = request.cookies.get(auth.SESSION_COOKIE)
    auth.invalidate_session(token)
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie(auth.SESSION_COOKIE)
    return resp


@app.post("/api/auth/change-pin")
async def api_change_pin(request: Request, body: ChangePinRequest):
    if body.new_pin != body.confirm_pin:
        raise HTTPException(400, "New PIN and confirmation do not match.")
    if len(body.new_pin) < 4:
        raise HTTPException(400, "PIN must be at least 4 characters.")
    with db.get_connection() as conn:
        settings = db.get_settings(conn)
    if not auth.verify_pin(body.current_pin, settings.get("pin_hash", "")):
        raise HTTPException(401, "Current PIN is incorrect.")
    with db.get_connection() as conn:
        db.update_setting(conn, "pin_hash", auth.hash_pin(body.new_pin))
    return {"ok": True}


# ── Helper ────────────────────────────────────────────────────────────────────

def _fmt_eur(cents: int) -> str:
    return f"€{cents / 100:,.2f}"


templates.env.filters["eur"] = _fmt_eur
templates.env.filters["abs"] = abs


# ── Pages ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def page_index(request: Request):
    with db.get_connection() as conn:
        accounts = db.get_accounts(conn)
        recent = db.get_transactions(conn, limit=10)
        settings = db.get_settings(conn)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "accounts": accounts,
        "recent": recent,
        "settings": settings,
        "today": Date.today().isoformat(),
    })


@app.get("/setup", response_class=HTMLResponse)
async def page_setup(request: Request):
    with db.get_connection() as conn:
        accounts = db.get_accounts(conn, active_only=False)
        expense_cats = db.get_categories(conn, "expense")
        income_cats = db.get_categories(conn, "income")
        settings = db.get_settings(conn)
    return templates.TemplateResponse("setup.html", {
        "request": request,
        "accounts": accounts,
        "expense_cats": expense_cats,
        "income_cats": income_cats,
        "settings": settings,
    })


@app.get("/entry", response_class=HTMLResponse)
async def page_entry(request: Request):
    with db.get_connection() as conn:
        accounts = db.get_accounts(conn)
        expense_cats = db.get_categories(conn, "expense")
        income_cats = db.get_categories(conn, "income")
        settings = db.get_settings(conn)
    return templates.TemplateResponse("entry.html", {
        "request": request,
        "accounts": accounts,
        "expense_cats": expense_cats,
        "income_cats": income_cats,
        "settings": settings,
        "today": Date.today().isoformat(),
    })


@app.get("/transactions", response_class=HTMLResponse)
async def page_transactions(request: Request):
    with db.get_connection() as conn:
        accounts = db.get_accounts(conn)
        expense_cats = db.get_categories(conn, "expense")
        income_cats = db.get_categories(conn, "income")
        settings = db.get_settings(conn)
    return templates.TemplateResponse("transactions.html", {
        "request": request,
        "accounts": accounts,
        "expense_cats": expense_cats,
        "income_cats": income_cats,
        "settings": settings,
        "today": Date.today().isoformat(),
    })


@app.get("/report", response_class=HTMLResponse)
async def page_report(
    request: Request,
    year: int = Query(default=None),
    month: int = Query(default=None),
):
    today = Date.today()
    if year is None:
        year = today.year
    if month is None:
        month = today.month

    with db.get_connection() as conn:
        data = db.get_monthly_data(conn, year, month)
        settings = db.get_settings(conn)

    import calendar as cal
    month_name = cal.month_name[month]
    return templates.TemplateResponse("report.html", {
        "request": request,
        "data": data,
        "month_name": month_name,
        "settings": settings,
        "year": year,
        "month": month,
        "today": today.isoformat(),
    })


@app.get("/export", response_class=HTMLResponse)
async def page_export(request: Request):
    with db.get_connection() as conn:
        settings = db.get_settings(conn)
    return templates.TemplateResponse("export.html", {"request": request, "settings": settings})


# ── API: Accounts ─────────────────────────────────────────────────────────────

@app.get("/api/accounts")
async def api_list_accounts(active_only: bool = True):
    with db.get_connection() as conn:
        return db.get_accounts(conn, active_only=active_only)


@app.post("/api/accounts", status_code=201)
async def api_create_account(body: AccountCreate):
    try:
        with db.get_connection() as conn:
            aid = db.create_account(conn, body.label, body.account_type,
                                    body.opening_balance_cents, body.opening_date)
            return db.get_account(conn, aid)
    except Exception as e:
        raise HTTPException(400, str(e))


@app.put("/api/accounts/{account_id}")
async def api_update_account(account_id: int, body: AccountUpdate):
    try:
        with db.get_connection() as conn:
            if not db.get_account(conn, account_id):
                raise HTTPException(404, "Account not found")
            db.update_account(conn, account_id, **body.model_dump(exclude_none=True))
            return db.get_account(conn, account_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))


@app.delete("/api/accounts/{account_id}")
async def api_delete_account(account_id: int, deactivate: bool = False):
    try:
        with db.get_connection() as conn:
            if not db.get_account(conn, account_id):
                raise HTTPException(404, "Account not found")
            if deactivate:
                db.update_account(conn, account_id, is_active=0)
            else:
                db.delete_account(conn, account_id)
        return {"ok": True}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(409, str(e))


# ── API: Categories ───────────────────────────────────────────────────────────

@app.get("/api/categories")
async def api_list_categories(transaction_type: Optional[str] = None):
    with db.get_connection() as conn:
        return db.get_categories(conn, transaction_type)


@app.post("/api/categories", status_code=201)
async def api_create_category(body: CategoryCreate):
    try:
        with db.get_connection() as conn:
            cid = db.create_category(conn, body.name, body.transaction_type)
            return {"id": cid, "name": body.name, "transaction_type": body.transaction_type}
    except Exception as e:
        raise HTTPException(400, str(e))


@app.put("/api/categories/{category_id}")
async def api_update_category(category_id: int, body: CategoryUpdate):
    try:
        with db.get_connection() as conn:
            db.update_category(conn, category_id, body.name)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(400, str(e))


@app.delete("/api/categories/{category_id}")
async def api_delete_category(category_id: int):
    try:
        with db.get_connection() as conn:
            db.delete_category(conn, category_id)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(409, str(e))


# ── API: Transactions ─────────────────────────────────────────────────────────

@app.get("/api/transactions")
async def api_list_transactions(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    transaction_type: Optional[str] = None,
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
):
    with db.get_connection() as conn:
        return db.get_transactions(
            conn, date_from=date_from, date_to=date_to,
            transaction_type=transaction_type, account_id=account_id,
            category_id=category_id, search=search,
            limit=limit, offset=offset,
        )


@app.post("/api/transactions", status_code=201)
async def api_create_transaction(body: TransactionCreate):
    try:
        with db.get_connection() as conn:
            tid = db.create_transaction(
                conn, body.date, body.transaction_type, body.amount_cents,
                body.from_account_id, body.to_account_id,
                body.category_id, body.description,
            )
            return db.get_transaction(conn, tid)
    except Exception as e:
        raise HTTPException(400, str(e))


@app.put("/api/transactions/{tx_id}")
async def api_update_transaction(tx_id: int, body: TransactionUpdate):
    try:
        with db.get_connection() as conn:
            if not db.get_transaction(conn, tx_id):
                raise HTTPException(404, "Transaction not found")
            db.update_transaction(conn, tx_id, **body.model_dump(exclude_none=True))
            return db.get_transaction(conn, tx_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))


@app.delete("/api/transactions/{tx_id}")
async def api_delete_transaction(tx_id: int):
    with db.get_connection() as conn:
        if not db.get_transaction(conn, tx_id):
            raise HTTPException(404, "Transaction not found")
        db.delete_transaction(conn, tx_id)
    return {"ok": True}


# ── API: Batch Entry ──────────────────────────────────────────────────────────

@app.post("/api/transactions/batch/preview")
async def api_batch_preview(body: BatchPreviewRequest):
    today = Date.today().isoformat()
    parsed = parse_batch(body.text, today)

    with db.get_connection() as conn:
        accounts = db.get_accounts(conn)
        categories = db.get_categories(conn)

    accounts_by_label = {a["label"].upper(): a for a in accounts}
    cats_by_name = {c["name"]: c for c in categories}

    results = []
    for item in parsed:
        if isinstance(item, ParseError):
            results.append({"ok": False, "raw": item.raw, "line": item.line_number, "error": item.message})
            continue

        resolved = resolve_entry(item, accounts_by_label, cats_by_name)
        if isinstance(resolved, str):
            results.append({"ok": False, "raw": item.raw, "line": 0, "error": resolved})
            continue

        with db.get_connection() as conn:
            try:
                db.validate_transaction(
                    conn,
                    resolved["transaction_type"],
                    resolved["amount_cents"],
                    resolved.get("from_account_id"),
                    resolved.get("to_account_id"),
                )
            except ValueError as e:
                results.append({"ok": False, "raw": item.raw, "line": 0, "error": str(e)})
                continue

            dups = db.check_duplicates(
                conn, resolved["date"], resolved["transaction_type"],
                resolved["amount_cents"],
                resolved.get("from_account_id"), resolved.get("to_account_id"),
            )

        results.append({
            "ok": True,
            "raw": item.raw,
            "resolved": resolved,
            "duplicate_ids": dups,
        })

    return {"entries": results}


@app.post("/api/transactions/batch/save", status_code=201)
async def api_batch_save(entries: list[dict]):
    """Save a list of pre-resolved transaction dicts (from preview confirm step)."""
    saved_ids = []
    errors = []
    with db.get_connection() as conn:
        for entry in entries:
            try:
                tid = db.create_transaction(
                    conn,
                    entry["date"],
                    entry["transaction_type"],
                    entry["amount_cents"],
                    entry.get("from_account_id"),
                    entry.get("to_account_id"),
                    entry.get("category_id"),
                    entry.get("description", ""),
                )
                saved_ids.append(tid)
            except Exception as e:
                errors.append({"entry": entry, "error": str(e)})
    return {"saved": saved_ids, "errors": errors}


# ── API: Charts ───────────────────────────────────────────────────────────────

def _get_monthly_data(year: int, month: int) -> dict:
    with db.get_connection() as conn:
        return db.get_monthly_data(conn, year, month)


@app.get("/api/charts/category-spending")
async def chart_category(year: int, month: int):
    data = _get_monthly_data(year, month)
    png = reports.chart_expense_by_category(data["expense_by_cat"])
    return Response(content=png, media_type="image/png")


@app.get("/api/charts/daily-spending")
async def chart_daily(year: int, month: int):
    data = _get_monthly_data(year, month)
    png = reports.chart_daily_spending(data["daily_spending"], year, month)
    return Response(content=png, media_type="image/png")


@app.get("/api/charts/income-expenses")
async def chart_income_expenses(year: int, month: int):
    data = _get_monthly_data(year, month)
    png = reports.chart_income_vs_expenses(data["income_total"], data["expense_total"])
    return Response(content=png, media_type="image/png")


@app.get("/api/charts/spending-by-account")
async def chart_by_account(year: int, month: int):
    data = _get_monthly_data(year, month)
    png = reports.chart_spending_by_account(data["spending_by_acct"])
    return Response(content=png, media_type="image/png")


# ── API: Settings ─────────────────────────────────────────────────────────────

@app.get("/api/settings")
async def api_get_settings():
    with db.get_connection() as conn:
        return db.get_settings(conn)


@app.put("/api/settings")
async def api_update_settings(body: SettingsUpdate):
    with db.get_connection() as conn:
        for key, value in body.model_dump(exclude_none=True).items():
            db.update_setting(conn, key, value)
    return {"ok": True}


# ── Export ────────────────────────────────────────────────────────────────────

@app.get("/api/export/csv")
async def export_csv(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    with db.get_connection() as conn:
        txns = db.get_transactions(conn, date_from=date_from, date_to=date_to, limit=100_000)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "id", "date", "type", "amount_eur", "amount_cents",
        "from_account", "to_account", "category", "description", "created_at",
    ])
    for t in txns:
        writer.writerow([
            t["id"], t["date"], t["transaction_type"],
            f"{t['amount_cents'] / 100:.2f}", t["amount_cents"],
            t.get("from_account_label", ""), t.get("to_account_label", ""),
            t.get("category_name", ""), t.get("description", ""),
            t.get("created_at", ""),
        ])

    buf.seek(0)
    filename = "transactions.csv"
    if date_from or date_to:
        filename = f"transactions_{date_from or 'start'}_{date_to or 'end'}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/export/db")
async def export_db():
    if not db.DB_PATH.exists():
        raise HTTPException(404, "Database not found")
    return FileResponse(
        path=db.DB_PATH,
        media_type="application/octet-stream",
        filename="expense_monitor.db",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
