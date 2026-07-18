"""Account lifecycle. Money movement lives in transaction_service."""
from __future__ import annotations

from decimal import Decimal

from app.db import read_only, unit_of_work
from app.repositories import accounts

from ._helpers import ensure_owner_or_admin, integrity_guard, new_id, utcnow
from .exceptions import NotFoundError

ADMIN = "ADMIN"


def create(customer_id: str, account_type: str, branch_id: str) -> dict:
    record = {
        "account_id": new_id(),
        "customer_id": customer_id,
        "account_type": account_type,
        "balance": Decimal("0.00"),
        "creation_date": utcnow(),
        "branch_id": branch_id,
    }
    with unit_of_work() as conn, integrity_guard():
        accounts.insert(conn, record)
    return record


def list_for_actor(actor: dict) -> list[dict]:
    """Admins see everything; customers see only their own accounts."""
    with read_only() as conn:
        if actor.get("role") == ADMIN:
            return accounts.list_all(conn)
        return accounts.list_by_customer(conn, actor.get("customer_id"))


def get(account_id: str, actor: dict) -> dict:
    with read_only() as conn:
        account = accounts.get(conn, account_id)
    if account is None:
        raise NotFoundError("Account not found")
    ensure_owner_or_admin(actor, account["customer_id"])
    return account


def set_balance(account_id: str, balance: Decimal) -> dict:
    balance = Decimal(balance).quantize(Decimal("0.01"))
    with unit_of_work() as conn, integrity_guard():
        if accounts.set_balance(conn, account_id, balance) == 0:
            raise NotFoundError("Account not found")
        return accounts.get(conn, account_id)


def delete(account_id: str) -> None:
    with unit_of_work() as conn, integrity_guard():
        if accounts.delete(conn, account_id) == 0:
            raise NotFoundError("Account not found")
