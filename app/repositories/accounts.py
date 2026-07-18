"""SQL for the account table, including the money-movement primitives.

``lock`` / ``debit`` / ``credit`` are the ledger operations a transfer composes
inside one unit of work. ``debit`` is guarded in SQL (``WHERE balance >= amount``)
so an overdraft cannot slip through a check-then-act race.
"""
from __future__ import annotations

from decimal import Decimal

from pymysql.connections import Connection

from ._base import execute, fetch_all, fetch_one

COLUMNS = "account_id, customer_id, account_type, balance, creation_date, branch_id"


def insert(conn: Connection, data: dict) -> None:
    execute(
        conn,
        "INSERT INTO account (account_id, customer_id, account_type, balance, "
        "creation_date, branch_id) VALUES (%(account_id)s, %(customer_id)s, "
        "%(account_type)s, %(balance)s, %(creation_date)s, %(branch_id)s)",
        data,
    )


def list_all(conn: Connection) -> list[dict]:
    return fetch_all(conn, f"SELECT {COLUMNS} FROM account")


def get(conn: Connection, account_id: str) -> dict | None:
    return fetch_one(
        conn, f"SELECT {COLUMNS} FROM account WHERE account_id = %s", (account_id,)
    )


def list_by_customer(conn: Connection, customer_id: str) -> list[dict]:
    return fetch_all(
        conn, f"SELECT {COLUMNS} FROM account WHERE customer_id = %s", (customer_id,)
    )


def set_balance(conn: Connection, account_id: str, balance: Decimal) -> int:
    return execute(
        conn,
        "UPDATE account SET balance = %s WHERE account_id = %s",
        (balance, account_id),
    )


def delete(conn: Connection, account_id: str) -> int:
    return execute(conn, "DELETE FROM account WHERE account_id = %s", (account_id,))


# --- ledger primitives (must run inside a unit of work) ---------------------


def lock(conn: Connection, account_id: str) -> dict | None:
    """Select a row FOR UPDATE, taking a write lock until the transaction ends."""
    return fetch_one(
        conn,
        f"SELECT {COLUMNS} FROM account WHERE account_id = %s FOR UPDATE",
        (account_id,),
    )


def debit(conn: Connection, account_id: str, amount: Decimal) -> int:
    """Subtract amount only if funds suffice. Returns rows affected (0 = declined)."""
    return execute(
        conn,
        "UPDATE account SET balance = balance - %s "
        "WHERE account_id = %s AND balance >= %s",
        (amount, account_id, amount),
    )


def credit(conn: Connection, account_id: str, amount: Decimal) -> int:
    return execute(
        conn,
        "UPDATE account SET balance = balance + %s WHERE account_id = %s",
        (amount, account_id),
    )
