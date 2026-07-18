"""SQL for the employee table."""
from __future__ import annotations

from pymysql.connections import Connection

from ._base import execute, fetch_all, fetch_one

COLUMNS = (
    "employee_id, branch_id, first_name, last_name, position, hire_date, "
    "phone_number, email"
)


def insert(conn: Connection, data: dict) -> None:
    execute(
        conn,
        "INSERT INTO employee (employee_id, branch_id, first_name, last_name, "
        "position, hire_date, phone_number, email) VALUES (%(employee_id)s, "
        "%(branch_id)s, %(first_name)s, %(last_name)s, %(position)s, "
        "%(hire_date)s, %(phone_number)s, %(email)s)",
        data,
    )


def list_all(conn: Connection) -> list[dict]:
    return fetch_all(conn, f"SELECT {COLUMNS} FROM employee")


def get(conn: Connection, employee_id: str) -> dict | None:
    return fetch_one(
        conn, f"SELECT {COLUMNS} FROM employee WHERE employee_id = %s", (employee_id,)
    )


def update(conn: Connection, employee_id: str, fields: dict) -> int:
    assignments = ", ".join(f"{col} = %({col})s" for col in fields)
    params = {**fields, "employee_id": employee_id}
    return execute(
        conn, f"UPDATE employee SET {assignments} WHERE employee_id = %(employee_id)s", params
    )


def delete(conn: Connection, employee_id: str) -> int:
    return execute(conn, "DELETE FROM employee WHERE employee_id = %s", (employee_id,))
