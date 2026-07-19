"""Connection pooling over PyMySQL.

A single process-wide pool is created lazily from Flask config and handed out
through :func:`get_connection`. Repositories never construct their own
connections; they receive one from the unit of work.
"""

from __future__ import annotations

import threading
from typing import Any

import pymysql.cursors
from dbutils.pooled_db import PooledDB
from flask import current_app

_pool: PooledDB | None = None
_lock = threading.Lock()


def _build_pool(config: Any) -> PooledDB:
    return PooledDB(
        creator=pymysql,
        maxconnections=config["DB_POOL_SIZE"],
        mincached=1,
        blocking=True,
        ping=1,  # check liveness when a connection is taken from the pool
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        database=config["DB_NAME"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def init_pool(config: Any) -> None:
    """Create the pool eagerly (called from the app factory)."""
    global _pool
    with _lock:
        _pool = _build_pool(config)


def get_pool() -> PooledDB:
    global _pool
    if _pool is None:
        with _lock:
            if _pool is None:
                _pool = _build_pool(current_app.config)
    return _pool


def get_connection():
    """Borrow a connection from the pool. Caller must close it to return it."""
    return get_pool().connection()


def reset_pool() -> None:
    """Drop the pool (used by tests to rebind to a fresh database)."""
    global _pool
    with _lock:
        _pool = None


def ping() -> bool:
    """Infrastructure liveness check for readiness probes."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return True
    finally:
        conn.close()
