"""SQL for the branch table, including the branch-conditions reporting query."""
from __future__ import annotations

from pymysql.connections import Connection

from ._base import execute, fetch_all, fetch_one

COLUMNS = (
    "branch_id, branch_name, address_line1, address_line2, city, zip_code, phone_number"
)


def insert(conn: Connection, data: dict) -> None:
    execute(
        conn,
        "INSERT INTO branch (branch_id, branch_name, address_line1, address_line2, "
        "city, zip_code, phone_number) VALUES (%(branch_id)s, %(branch_name)s, "
        "%(address_line1)s, %(address_line2)s, %(city)s, %(zip_code)s, %(phone_number)s)",
        data,
    )


def list_all(conn: Connection) -> list[dict]:
    return fetch_all(conn, f"SELECT {COLUMNS} FROM branch")


def get(conn: Connection, branch_id: str) -> dict | None:
    return fetch_one(conn, f"SELECT {COLUMNS} FROM branch WHERE branch_id = %s", (branch_id,))


def update(conn: Connection, branch_id: str, fields: dict) -> int:
    assignments = ", ".join(f"{col} = %({col})s" for col in fields)
    params = {**fields, "branch_id": branch_id}
    return execute(
        conn, f"UPDATE branch SET {assignments} WHERE branch_id = %(branch_id)s", params
    )


def delete(conn: Connection, branch_id: str) -> int:
    return execute(conn, "DELETE FROM branch WHERE branch_id = %s", (branch_id,))


def with_conditions(conn: Connection, min_employees: int, min_accounts: int) -> list[dict]:
    """Branches staffed and utilized above given thresholds.

    Analytical query 2 of 3: two LEFT JOINs fanning out to employees and
    accounts, de-duplicated with COUNT(DISTINCT ...), filtered with HAVING.
    """
    return fetch_all(
        conn,
        """
        SELECT B.branch_name,
               COUNT(DISTINCT E.employee_id) AS employee_count,
               COUNT(DISTINCT A.account_id) AS account_count
        FROM branch B
        LEFT JOIN employee E ON B.branch_id = E.branch_id
        LEFT JOIN account A ON B.branch_id = A.branch_id
        GROUP BY B.branch_name
        HAVING COUNT(DISTINCT E.employee_id) > %s AND COUNT(DISTINCT A.account_id) >= %s
        """,
        (min_employees, min_accounts),
    )
