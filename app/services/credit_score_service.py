"""Credit scores. Customers may read their own; admins manage all."""
from __future__ import annotations

from app.db import read_only, unit_of_work
from app.repositories import credit_scores

from ._helpers import ensure_owner_or_admin, integrity_guard, new_id
from .exceptions import NotFoundError


def create(data: dict) -> dict:
    record = {"credit_score_id": new_id(), **data}
    record.setdefault("computed_by_system", True)
    with unit_of_work() as conn, integrity_guard():
        credit_scores.insert(conn, record)
    return record


def list_all() -> list[dict]:
    with read_only() as conn:
        return credit_scores.list_all(conn)


def get(credit_score_id: str, actor: dict) -> dict:
    with read_only() as conn:
        score = credit_scores.get(conn, credit_score_id)
    if score is None:
        raise NotFoundError("Credit score not found")
    ensure_owner_or_admin(actor, score["customer_id"])
    return score


def update(credit_score_id: str, fields: dict) -> dict:
    with unit_of_work() as conn, integrity_guard():
        if credit_scores.update(conn, credit_score_id, fields) == 0:
            raise NotFoundError("Credit score not found")
        return credit_scores.get(conn, credit_score_id)


def delete(credit_score_id: str) -> None:
    with unit_of_work() as conn, integrity_guard():
        if credit_scores.delete(conn, credit_score_id) == 0:
            raise NotFoundError("Credit score not found")
