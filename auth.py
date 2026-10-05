"""PIN-based authentication for Expense Monitor.

Uses PBKDF2-HMAC-SHA256 (built-in hashlib) to store the PIN hash.
Sessions are kept in memory — they are lost on app restart, which is
acceptable for a single-user local app.
"""

import hashlib
import hmac
import secrets
import time
from typing import Optional

SESSION_COOKIE = "em_session"
SESSION_HOURS = 8      # session lifetime
LOCKOUT_AFTER = 3      # wrong attempts before cooldown
LOCKOUT_SECONDS = 30   # cooldown duration
PBKDF2_ITER = 100_000

_sessions: dict = {}   # token → expiry timestamp
_failed: int = 0       # consecutive wrong attempts
_lockout_until: float = 0.0


# ── Hashing ────────────────────────────────────────────────────────────────────

def hash_pin(pin: str) -> str:
    """Return 'salt:digest' suitable for storing in the settings table."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt.encode(), PBKDF2_ITER)
    return f"{salt}:{dk.hex()}"


def verify_pin(pin: str, stored: str) -> bool:
    """Constant-time comparison to avoid timing attacks."""
    try:
        salt, expected = stored.split(":", 1)
        dk = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt.encode(), PBKDF2_ITER)
        return hmac.compare_digest(dk.hex(), expected)
    except Exception:
        return False


# ── Lockout ────────────────────────────────────────────────────────────────────

def check_lockout() -> tuple:
    """Return (is_locked: bool, seconds_remaining: int)."""
    remaining = _lockout_until - time.time()
    if remaining > 0:
        return True, int(remaining) + 1
    return False, 0


def record_failure() -> None:
    global _failed, _lockout_until
    _failed += 1
    if _failed >= LOCKOUT_AFTER:
        _lockout_until = time.time() + LOCKOUT_SECONDS
        _failed = 0


def record_success() -> None:
    global _failed, _lockout_until
    _failed = 0
    _lockout_until = 0.0


# ── Sessions ───────────────────────────────────────────────────────────────────

def create_session() -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = time.time() + SESSION_HOURS * 3600
    return token


def is_valid_session(token: Optional[str]) -> bool:
    if not token:
        return False
    expiry = _sessions.get(token)
    if expiry is None:
        return False
    if time.time() > expiry:
        _sessions.pop(token, None)
        return False
    return True


def invalidate_session(token: Optional[str]) -> None:
    _sessions.pop(token or "", None)
