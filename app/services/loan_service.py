"""Loans. Customers may read their own; admins manage all."""
from __future__ import annotations

from app.db import read_only, unit_of_work
from app.repositories import loans

from ._helpers import ensure_owner_or_admin, integrity_guard, new_id
from .exceptions import NotFoundError

VALID_STATUSES = ("ACTIVE", "PAID_OFF", "DEFAULT")


def create(data: dict) -> dict:
    record = {"loan_id": new_id(), **data}
    record.setdefault("status", "ACTIVE")
    with unit_of_work() as conn, integrity_guard():
        loans.insert(conn, record)
    return record


def list_all() -> list[dict]:
    with read_only() as conn:
        return loans.list_all(conn)


def get(loan_id: str, actor: dict) -> dict:
    with read_only() as conn:
        loan = loans.get(conn, loan_id)
    if loan is None:
        raise NotFoundError("Loan not found")
    ensure_owner_or_admin(actor, loan["customer_id"])
    return loan


def set_status(loan_id: str, status: str) -> dict:
    with unit_of_work() as conn, integrity_guard():
        if loans.set_status(conn, loan_id, status) == 0:
            raise NotFoundError("Loan not found")
        return loans.get(conn, loan_id)


def delete(loan_id: str) -> None:
    with unit_of_work() as conn, integrity_guard():
        if loans.delete(conn, loan_id) == 0:
            raise NotFoundError("Loan not found")
