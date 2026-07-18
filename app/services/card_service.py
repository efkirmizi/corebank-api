"""Cards. Customers may view and block/unblock cards on their own accounts."""
from __future__ import annotations

from app.db import read_only, unit_of_work
from app.repositories import cards

from ._helpers import ensure_owner_or_admin, integrity_guard, new_id
from .exceptions import NotFoundError


def create(data: dict) -> dict:
    record = {"card_id": new_id(), **data}
    with unit_of_work() as conn, integrity_guard():
        cards.insert(conn, record)
    # Never echo the full PAN/CVV back; return the masked view.
    with read_only() as conn:
        return cards.get(conn, record["card_id"])


def list_all() -> list[dict]:
    with read_only() as conn:
        return cards.list_all(conn)


def get(card_id: str, actor: dict) -> dict:
    with read_only() as conn:
        owned = cards.get_with_account(conn, card_id)
        if owned is None:
            raise NotFoundError("Card not found")
        ensure_owner_or_admin(actor, owned["customer_id"])
        return cards.get(conn, card_id)


def set_status(card_id: str, status: str, actor: dict) -> dict:
    with unit_of_work() as conn, integrity_guard():
        owned = cards.get_with_account(conn, card_id)
        if owned is None:
            raise NotFoundError("Card not found")
        ensure_owner_or_admin(actor, owned["customer_id"])
        cards.set_status(conn, card_id, status)
        return cards.get(conn, card_id)


def delete(card_id: str) -> None:
    with unit_of_work() as conn, integrity_guard():
        if cards.delete(conn, card_id) == 0:
            raise NotFoundError("Card not found")
