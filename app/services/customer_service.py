"""Customer records. Customers may read and update their own; admins manage all."""
from __future__ import annotations

from app.db import read_only, unit_of_work
from app.repositories import customers

from ._helpers import ensure_owner_or_admin, integrity_guard, new_id
from .exceptions import NotFoundError


def create(data: dict) -> dict:
    record = {"customer_id": new_id(), **data}
    record.setdefault("address_line2", None)
    record.setdefault("wage_declaration", 0)
    with unit_of_work() as conn, integrity_guard():
        customers.insert(conn, record)
    return record


def list_all() -> list[dict]:
    with read_only() as conn:
        return customers.list_all(conn)


def get(customer_id: str, actor: dict) -> dict:
    ensure_owner_or_admin(actor, customer_id)
    with read_only() as conn:
        customer = customers.get(conn, customer_id)
    if customer is None:
        raise NotFoundError("Customer not found")
    return customer


def update(customer_id: str, fields: dict, actor: dict) -> dict:
    ensure_owner_or_admin(actor, customer_id)
    with unit_of_work() as conn, integrity_guard():
        if customers.update(conn, customer_id, fields) == 0:
            raise NotFoundError("Customer not found")
        return customers.get(conn, customer_id)


def delete(customer_id: str) -> None:
    with unit_of_work() as conn, integrity_guard():
        if customers.delete(conn, customer_id) == 0:
            raise NotFoundError("Customer not found")
