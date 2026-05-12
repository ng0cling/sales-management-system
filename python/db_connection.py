"""
PROJECT 03: SALES MANAGEMENT SYSTEM
File: db_connection.py
Database connection and base repository layer
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Generator

from dotenv import load_dotenv

load_dotenv()  # load .env trước khi đọc bất kỳ env var nào

from mysql.connector import Error, MySQLConnection
from mysql.connector.cursor import MySQLCursorDict
from mysql.connector.pooling import MySQLConnectionPool


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _require_env(key: str) -> str:
    """Read a required env var — raise clearly if it is missing or empty."""
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Required environment variable '{key}' is not set.")
    return val


def _env(key: str, default: str) -> str:
    return os.getenv(key, default)


# ─── Configuration ────────────────────────────────────────────────────────────

@dataclass
class DBConfig:
    # Optional env vars — sensible defaults are fine for non-sensitive values
    host:      str = field(default_factory=lambda: _env("DB_HOST", "localhost"))
    port:      int = field(default_factory=lambda: int(_env("DB_PORT", "3306")))
    user:      str = field(default_factory=lambda: _env("DB_USER", "app_user"))
    database:  str = field(default_factory=lambda: _env("DB_NAME", "sales_management"))
    pool_name: str = "sales_pool"
    pool_size: int = 5

    # Required — no fallback; app must not start without an explicit password
    password: str = field(default_factory=lambda: _require_env("DB_PASSWORD"))


# ─── Pool (lazy) ──────────────────────────────────────────────────────────────

_config: DBConfig | None = None
_pool:   MySQLConnectionPool | None = None


def get_config() -> DBConfig:
    """Return the singleton DBConfig, initialised on first call.

    Lazy init ensures env vars (e.g. loaded via python-dotenv) are already
    present by the time we read them, regardless of import order.
    """
    global _config
    if _config is None:
        _config = DBConfig()
    return _config


def _get_pool() -> MySQLConnectionPool:
    """Return the singleton connection pool, created on first call."""
    global _pool
    if _pool is None:
        cfg = get_config()
        _pool = MySQLConnectionPool(
            pool_name=cfg.pool_name,
            pool_size=cfg.pool_size,
            host=cfg.host,
            port=cfg.port,
            user=cfg.user,
            password=cfg.password,
            database=cfg.database,
            autocommit=False,
            charset="utf8mb4",
        )
    return _pool


def get_connection() -> MySQLConnection:
    """Return a pooled connection (caller is responsible for closing)."""
    return _get_pool().get_connection()


# ─── Context manager ──────────────────────────────────────────────────────────

@contextmanager
def db_cursor(
    *, commit: bool = False
) -> Generator[tuple[MySQLConnection, MySQLCursorDict], None, None]:
    """Context manager that yields (conn, cursor) and optionally commits.

    Usage:
        with db_cursor(commit=True) as (conn, cursor):
            cursor.execute("INSERT INTO ...")

    - On success with commit=True  → commits automatically.
    - On any Error                 → rolls back and re-raises with original traceback.
    - Always                       → returns connection to the pool via close().
    """
    conn: MySQLConnection = get_connection()
    cursor: MySQLCursorDict = conn.cursor(dictionary=True)  # type: ignore[assignment]
    try:
        yield conn, cursor
        if commit:
            conn.commit()
    except Error:
        conn.rollback()
        raise           # bare raise — preserves original traceback
    finally:
        cursor.close()
        conn.close()    # returns connection to pool, does not physically close it