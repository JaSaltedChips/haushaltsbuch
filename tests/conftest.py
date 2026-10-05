"""Shared test fixtures — in-memory SQLite database."""

import sqlite3
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import database as db


def make_test_db():
    """Create and return an in-memory SQLite connection with schema + defaults."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(db.SCHEMA)
    db._seed_defaults(conn)
    conn.commit()
    return conn


@pytest.fixture
def conn():
    c = make_test_db()
    yield c
    c.close()


@pytest.fixture
def account_ids(conn):
    """Return a dict mapping default account labels to their IDs."""
    rows = conn.execute("SELECT id, label FROM accounts").fetchall()
    return {r["label"]: r["id"] for r in rows}
