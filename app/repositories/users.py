"""SQL for the user table. Password hashes are stored, never plaintext."""

from __future__ import annotations

from pymysql.connections import Connection

from ._base import execute, fetch_all, fetch_one

# Safe columns — never selects the password hash into general responses.
PUBLIC_COLUMNS = "user_id, username, role, customer_id"


def insert(conn: Connection, data: dict) -> None:
    execute(
        conn,
        "INSERT INTO user (user_id, username, password, role, customer_id) "
        "VALUES (%(user_id)s, %(username)s, %(password)s, %(role)s, %(customer_id)s)",
        data,
    )


def get_by_username(conn: Connection, username: str) -> dict | None:
    """Includes the password hash — used only by authentication."""
    return fetch_one(
        conn,
        "SELECT user_id, username, password, role, customer_id FROM user WHERE username = %s",
        (username,),
    )


def list_all(conn: Connection) -> list[dict]:
    return fetch_all(conn, f"SELECT {PUBLIC_COLUMNS} FROM user")


def get(conn: Connection, user_id: str) -> dict | None:
    return fetch_one(conn, f"SELECT {PUBLIC_COLUMNS} FROM user WHERE user_id = %s", (user_id,))


def update(conn: Connection, user_id: str, fields: dict) -> int:
    assignments = ", ".join(f"{col} = %({col})s" for col in fields)
    params = {**fields, "user_id": user_id}
    return execute(conn, f"UPDATE user SET {assignments} WHERE user_id = %(user_id)s", params)


def delete(conn: Connection, user_id: str) -> int:
    return execute(conn, "DELETE FROM user WHERE user_id = %s", (user_id,))
