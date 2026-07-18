"""Loan payments. Admin-managed; readable per loan."""
from __future__ import annotations

from app.db import read_only, unit_of_work
from app.repositories import loan_payments, loans

from ._helpers import integrity_guard, new_id, utcnow
from .exceptions import NotFoundError


def create(data: dict) -> dict:
    record = {"loan_payment_id": new_id(), **data}
    record.setdefault("payment_date", utcnow())
    record.setdefault("remaining_balance", None)
    with unit_of_work() as conn, integrity_guard():
        loan_payments.insert(conn, record)
    return record


def list_all() -> list[dict]:
    with read_only() as conn:
        return loan_payments.list_all(conn)


def get(loan_payment_id: str) -> dict:
    with read_only() as conn:
        payment = loan_payments.get(conn, loan_payment_id)
    if payment is None:
        raise NotFoundError("Loan payment not found")
    return payment


def list_by_loan(loan_id: str) -> list[dict]:
    with read_only() as conn:
        if loans.get(conn, loan_id) is None:
            raise NotFoundError("Loan not found")
        return loan_payments.list_by_loan(conn, loan_id)


def delete(loan_payment_id: str) -> None:
    with unit_of_work() as conn, integrity_guard():
        if loan_payments.delete(conn, loan_payment_id) == 0:
            raise NotFoundError("Loan payment not found")
