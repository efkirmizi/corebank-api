"""Customer-support tickets, plus the top-resolvers report.

Customers open tickets for themselves and read their own; admins see all, change
status, and view the reporting query.
"""
from __future__ import annotations

from app.db import read_only, unit_of_work
from app.repositories import support_tickets

from ._helpers import ensure_owner_or_admin, integrity_guard, new_id, utcnow
from .exceptions import NotFoundError


def create(customer_id: str, employee_id: str, issue_description: str) -> dict:
    record = {
        "ticket_id": new_id(),
        "customer_id": customer_id,
        "employee_id": employee_id,
        "issue_description": issue_description,
        "status": "OPEN",
        "created_date": utcnow(),
        "resolved_date": None,
    }
    with unit_of_work() as conn, integrity_guard():
        support_tickets.insert(conn, record)
    return record


def list_all() -> list[dict]:
    with read_only() as conn:
        return support_tickets.list_all(conn)


def get(ticket_id: str, actor: dict) -> dict:
    with read_only() as conn:
        ticket = support_tickets.get(conn, ticket_id)
    if ticket is None:
        raise NotFoundError("Ticket not found")
    ensure_owner_or_admin(actor, ticket["customer_id"])
    return ticket


def set_status(ticket_id: str, status: str) -> dict:
    resolved_date = utcnow() if status == "RESOLVED" else None
    with unit_of_work() as conn, integrity_guard():
        if support_tickets.set_status(conn, ticket_id, status, resolved_date) == 0:
            raise NotFoundError("Ticket not found")
        return support_tickets.get(conn, ticket_id)


def delete(ticket_id: str) -> None:
    with unit_of_work() as conn, integrity_guard():
        if support_tickets.delete(conn, ticket_id) == 0:
            raise NotFoundError("Ticket not found")


def top_resolvers() -> list[dict]:
    with read_only() as conn:
        return support_tickets.top_resolvers(conn)
