"""SQL for the transaction ledger, including the high-value reporting query."""

from __future__ import annotations

from pymysql.connections import Connection

from ._base import execute, fetch_all, fetch_one

COLUMNS = (
    "transaction_id, from_account_id, to_account_id, transaction_type, amount, "
    "transaction_timestamp"
)


def insert(conn: Connection, data: dict) -> None:
    execute(
        conn,
        "INSERT INTO transaction (transaction_id, from_account_id, to_account_id, "
        "transaction_type, amount, transaction_timestamp) VALUES "
        "(%(transaction_id)s, %(from_account_id)s, %(to_account_id)s, "
        "%(transaction_type)s, %(amount)s, %(transaction_timestamp)s)",
        data,
    )


def list_all(conn: Connection) -> list[dict]:
    return fetch_all(conn, f"SELECT {COLUMNS} FROM transaction ORDER BY transaction_timestamp DESC")


def get(conn: Connection, transaction_id: str) -> dict | None:
    return fetch_one(
        conn, f"SELECT {COLUMNS} FROM transaction WHERE transaction_id = %s", (transaction_id,)
    )


def list_by_account(conn: Connection, account_id: str) -> list[dict]:
    return fetch_all(
        conn,
        f"SELECT {COLUMNS} FROM transaction "
        "WHERE from_account_id = %s OR to_account_id = %s "
        "ORDER BY transaction_timestamp DESC",
        (account_id, account_id),
    )


def delete(conn: Connection, transaction_id: str) -> int:
    return execute(conn, "DELETE FROM transaction WHERE transaction_id = %s", (transaction_id,))


def customers_with_high_transactions(conn: Connection, minimum) -> list[dict]:
    """Customers whose transactions (in or out) sum above a threshold.

    Analytical query 1 of 3: aggregate across accounts per customer and filter
    the grouped total with HAVING.
    """
    return fetch_all(
        conn,
        """
        SELECT C.customer_id, C.first_name, C.last_name, SUM(T.amount) AS total_transaction
        FROM customer C
        JOIN account A ON C.customer_id = A.customer_id
        JOIN transaction T ON A.account_id = T.from_account_id OR A.account_id = T.to_account_id
        GROUP BY C.customer_id, C.first_name, C.last_name
        HAVING SUM(T.amount) > %s
        ORDER BY total_transaction DESC
        """,
        (minimum,),
    )
