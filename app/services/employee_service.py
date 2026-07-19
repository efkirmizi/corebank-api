"""Employees. Admin-managed."""

from __future__ import annotations

from app.db import read_only, unit_of_work
from app.repositories import employees

from ._helpers import integrity_guard, new_id
from .exceptions import NotFoundError


def create(data: dict) -> dict:
    record = {"employee_id": new_id(), **data}
    with unit_of_work() as conn, integrity_guard():
        employees.insert(conn, record)
    return record


def list_all() -> list[dict]:
    with read_only() as conn:
        return employees.list_all(conn)


def get(employee_id: str) -> dict:
    with read_only() as conn:
        employee = employees.get(conn, employee_id)
    if employee is None:
        raise NotFoundError("Employee not found")
    return employee


def update(employee_id: str, fields: dict) -> dict:
    with unit_of_work() as conn, integrity_guard():
        if employees.update(conn, employee_id, fields) == 0:
            raise NotFoundError("Employee not found")
        return employees.get(conn, employee_id)


def delete(employee_id: str) -> None:
    with unit_of_work() as conn, integrity_guard():
        if employees.delete(conn, employee_id) == 0:
            raise NotFoundError("Employee not found")
