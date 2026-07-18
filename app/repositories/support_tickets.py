"""SQL for the customer_support table, including the top-resolvers query."""
from __future__ import annotations

from pymysql.connections import Connection

from ._base import execute, fetch_all, fetch_one

COLUMNS = (
    "ticket_id, customer_id, employee_id, issue_description, status, "
    "created_date, resolved_date"
)


def insert(conn: Connection, data: dict) -> None:
    execute(
        conn,
        "INSERT INTO customer_support (ticket_id, customer_id, employee_id, "
        "issue_description, status, created_date, resolved_date) VALUES "
        "(%(ticket_id)s, %(customer_id)s, %(employee_id)s, %(issue_description)s, "
        "%(status)s, %(created_date)s, %(resolved_date)s)",
        data,
    )


def list_all(conn: Connection) -> list[dict]:
    return fetch_all(conn, f"SELECT {COLUMNS} FROM customer_support")


def get(conn: Connection, ticket_id: str) -> dict | None:
    return fetch_one(
        conn, f"SELECT {COLUMNS} FROM customer_support WHERE ticket_id = %s", (ticket_id,)
    )


def set_status(conn: Connection, ticket_id: str, status: str, resolved_date) -> int:
    return execute(
        conn,
        "UPDATE customer_support SET status = %s, resolved_date = %s WHERE ticket_id = %s",
        (status, resolved_date, ticket_id),
    )


def delete(conn: Connection, ticket_id: str) -> int:
    return execute(conn, "DELETE FROM customer_support WHERE ticket_id = %s", (ticket_id,))


def top_resolvers(conn: Connection) -> list[dict]:
    """Employees tied for the most resolved tickets.

    Analytical query 3 of 3: a CTE aggregates resolved counts per employee, then
    the outer query keeps only those matching the maximum.
    """
    return fetch_all(
        conn,
        """
        WITH ResolvedTickets AS (
            SELECT E.employee_id, E.first_name, E.last_name,
                   COUNT(CS.ticket_id) AS resolved_tickets
            FROM employee E
            JOIN customer_support CS ON E.employee_id = CS.employee_id
            WHERE CS.status = 'RESOLVED'
            GROUP BY E.employee_id, E.first_name, E.last_name
        )
        SELECT employee_id, first_name, last_name, resolved_tickets
        FROM ResolvedTickets
        WHERE resolved_tickets = (SELECT MAX(resolved_tickets) FROM ResolvedTickets)
        """,
    )
