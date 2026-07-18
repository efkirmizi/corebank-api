"""Thin cursor helpers shared by repositories.

They remove open/execute/fetch/close boilerplate while keeping every SQL string
explicit and visible in the calling repository — the SQL is the point, so it is
never hidden behind query-builder magic.
"""
from __future__ import annotations

from typing import Any, Sequence

from pymysql.connections import Connection

Params = Sequence[Any]


def fetch_one(conn: Connection, sql: str, params: Params = ()) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def fetch_all(conn: Connection, sql: str, params: Params = ()) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def execute(conn: Connection, sql: str, params: Params = ()) -> int:
    """Run a write and return the affected row count."""
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.rowcount
