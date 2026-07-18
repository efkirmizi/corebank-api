"""SQL for the loan_payment table."""
from __future__ import annotations

from pymysql.connections import Connection

from ._base import execute, fetch_all, fetch_one

COLUMNS = "loan_payment_id, loan_id, payment_date, payment_amount, remaining_balance"


def insert(conn: Connection, data: dict) -> None:
    execute(
        conn,
        "INSERT INTO loan_payment (loan_payment_id, loan_id, payment_date, "
        "payment_amount, remaining_balance) VALUES (%(loan_payment_id)s, "
        "%(loan_id)s, %(payment_date)s, %(payment_amount)s, %(remaining_balance)s)",
        data,
    )


def list_all(conn: Connection) -> list[dict]:
    return fetch_all(conn, f"SELECT {COLUMNS} FROM loan_payment")


def get(conn: Connection, loan_payment_id: str) -> dict | None:
    return fetch_one(
        conn,
        f"SELECT {COLUMNS} FROM loan_payment WHERE loan_payment_id = %s",
        (loan_payment_id,),
    )


def list_by_loan(conn: Connection, loan_id: str) -> list[dict]:
    return fetch_all(
        conn,
        f"SELECT {COLUMNS} FROM loan_payment WHERE loan_id = %s ORDER BY payment_date",
        (loan_id,),
    )


def delete(conn: Connection, loan_payment_id: str) -> int:
    return execute(
        conn, "DELETE FROM loan_payment WHERE loan_payment_id = %s", (loan_payment_id,)
    )
