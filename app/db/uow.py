"""Unit of work.

The single transaction boundary in the system. Services open a unit of work,
call one or more repositories with the shared connection, and either everything
commits or everything rolls back. Repositories never commit on their own — that
is what makes a partial money transfer structurally impossible.

    with unit_of_work() as conn:
        accounts.debit(conn, sender_id, amount)
        accounts.credit(conn, receiver_id, amount)
        transactions.record(conn, ...)
    # COMMIT here, or ROLLBACK if the block raised
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from pymysql.connections import Connection

from .pool import get_connection


@contextmanager
def unit_of_work() -> Iterator[Connection]:
    conn = get_connection()
    try:
        conn.begin()
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()  # returns the connection to the pool


@contextmanager
def read_only() -> Iterator[Connection]:
    """A connection for pure reads. No explicit transaction is committed."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
