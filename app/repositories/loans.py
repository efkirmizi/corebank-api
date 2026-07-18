"""SQL for the loan table."""
from __future__ import annotations

from pymysql.connections import Connection

from ._base import execute, fetch_all, fetch_one

COLUMNS = (
    "loan_id, customer_id, loan_type, principal_amount, interest_rate, "
    "start_date, end_date, status"
)


def insert(conn: Connection, data: dict) -> None:
    execute(
        conn,
        "INSERT INTO loan (loan_id, customer_id, loan_type, principal_amount, "
        "interest_rate, start_date, end_date, status) VALUES (%(loan_id)s, "
        "%(customer_id)s, %(loan_type)s, %(principal_amount)s, %(interest_rate)s, "
        "%(start_date)s, %(end_date)s, %(status)s)",
        data,
    )


def list_all(conn: Connection) -> list[dict]:
    return fetch_all(conn, f"SELECT {COLUMNS} FROM loan")


def get(conn: Connection, loan_id: str) -> dict | None:
    return fetch_one(conn, f"SELECT {COLUMNS} FROM loan WHERE loan_id = %s", (loan_id,))


def set_status(conn: Connection, loan_id: str, status: str) -> int:
    return execute(conn, "UPDATE loan SET status = %s WHERE loan_id = %s", (status, loan_id))


def delete(conn: Connection, loan_id: str) -> int:
    return execute(conn, "DELETE FROM loan WHERE loan_id = %s", (loan_id,))
