"""Branches. Admin-managed, plus the branch-conditions report."""
from __future__ import annotations

from app.db import read_only, unit_of_work
from app.repositories import branches

from ._helpers import integrity_guard, new_id
from .exceptions import NotFoundError


def create(data: dict) -> dict:
    record = {"branch_id": new_id(), **data}
    record.setdefault("address_line2", None)
    with unit_of_work() as conn, integrity_guard():
        branches.insert(conn, record)
    return record


def list_all() -> list[dict]:
    with read_only() as conn:
        return branches.list_all(conn)


def get(branch_id: str) -> dict:
    with read_only() as conn:
        branch = branches.get(conn, branch_id)
    if branch is None:
        raise NotFoundError("Branch not found")
    return branch


def update(branch_id: str, fields: dict) -> dict:
    with unit_of_work() as conn, integrity_guard():
        if branches.update(conn, branch_id, fields) == 0:
            raise NotFoundError("Branch not found")
        return branches.get(conn, branch_id)


def delete(branch_id: str) -> None:
    with unit_of_work() as conn, integrity_guard():
        if branches.delete(conn, branch_id) == 0:
            raise NotFoundError("Branch not found")


def with_conditions(min_employees: int, min_accounts: int) -> list[dict]:
    with read_only() as conn:
        return branches.with_conditions(conn, min_employees, min_accounts)
