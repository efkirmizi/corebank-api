"""SQL for the card table."""

from __future__ import annotations

from pymysql.connections import Connection

from ._base import execute, fetch_all, fetch_one

COLUMNS = "card_id, account_id, card_type, card_number, expiration_date, cvv, status"
# Card number and CVV are sensitive; general listings expose only the last four.
SAFE_COLUMNS = (
    "card_id, account_id, card_type, "
    "CONCAT('************', RIGHT(card_number, 4)) AS card_number, "
    "expiration_date, status"
)


def insert(conn: Connection, data: dict) -> None:
    execute(
        conn,
        "INSERT INTO card (card_id, account_id, card_type, card_number, "
        "expiration_date, cvv, status) VALUES (%(card_id)s, %(account_id)s, "
        "%(card_type)s, %(card_number)s, %(expiration_date)s, %(cvv)s, %(status)s)",
        data,
    )


def list_all(conn: Connection) -> list[dict]:
    return fetch_all(conn, f"SELECT {SAFE_COLUMNS} FROM card")


def get(conn: Connection, card_id: str) -> dict | None:
    return fetch_one(conn, f"SELECT {SAFE_COLUMNS} FROM card WHERE card_id = %s", (card_id,))


def get_with_account(conn: Connection, card_id: str) -> dict | None:
    """Includes account_id and customer_id for ownership checks."""
    return fetch_one(
        conn,
        "SELECT c.card_id, c.account_id, a.customer_id, c.status "
        "FROM card c JOIN account a ON c.account_id = a.account_id "
        "WHERE c.card_id = %s",
        (card_id,),
    )


def set_status(conn: Connection, card_id: str, status: str) -> int:
    return execute(conn, "UPDATE card SET status = %s WHERE card_id = %s", (status, card_id))


def delete(conn: Connection, card_id: str) -> int:
    return execute(conn, "DELETE FROM card WHERE card_id = %s", (card_id,))
