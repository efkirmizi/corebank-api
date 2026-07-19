"""SQL for the customer table."""

from __future__ import annotations

from pymysql.connections import Connection

from ._base import execute, fetch_all, fetch_one

COLUMNS = (
    "customer_id, first_name, last_name, date_of_birth, phone_number, email, "
    "address_line1, address_line2, city, zip_code, wage_declaration"
)


def insert(conn: Connection, data: dict) -> None:
    execute(
        conn,
        f"INSERT INTO customer ({COLUMNS}) VALUES "
        "(%(customer_id)s, %(first_name)s, %(last_name)s, %(date_of_birth)s, "
        "%(phone_number)s, %(email)s, %(address_line1)s, %(address_line2)s, "
        "%(city)s, %(zip_code)s, %(wage_declaration)s)",
        data,
    )


def list_all(conn: Connection) -> list[dict]:
    return fetch_all(conn, f"SELECT {COLUMNS} FROM customer")


def get(conn: Connection, customer_id: str) -> dict | None:
    return fetch_one(conn, f"SELECT {COLUMNS} FROM customer WHERE customer_id = %s", (customer_id,))


def update(conn: Connection, customer_id: str, fields: dict) -> int:
    assignments = ", ".join(f"{col} = %({col})s" for col in fields)
    params = {**fields, "customer_id": customer_id}
    return execute(
        conn, f"UPDATE customer SET {assignments} WHERE customer_id = %(customer_id)s", params
    )


def delete(conn: Connection, customer_id: str) -> int:
    return execute(conn, "DELETE FROM customer WHERE customer_id = %s", (customer_id,))
