"""User accounts (login identities). Admin-managed.

Passwords are hashed with werkzeug before storage and never returned. Unlike the
original, creating a user is an admin-only operation at the API layer — the old
endpoint was unauthenticated, so anyone could mint an ADMIN account.
"""
from __future__ import annotations

from werkzeug.security import generate_password_hash

from app.db import read_only, unit_of_work
from app.repositories import users

from ._helpers import integrity_guard, new_id
from .exceptions import NotFoundError


def _public(user: dict) -> dict:
    return {k: user[k] for k in ("user_id", "username", "role", "customer_id")}


def create(username: str, password: str, role: str, customer_id: str | None) -> dict:
    record = {
        "user_id": new_id(),
        "username": username,
        "password": generate_password_hash(password),
        "role": role,
        "customer_id": customer_id,
    }
    with unit_of_work() as conn, integrity_guard():
        users.insert(conn, record)
    return _public(record)


def list_all() -> list[dict]:
    with read_only() as conn:
        return users.list_all(conn)


def get(user_id: str) -> dict:
    with read_only() as conn:
        user = users.get(conn, user_id)
    if user is None:
        raise NotFoundError("User not found")
    return user


def update(user_id: str, fields: dict) -> dict:
    fields = dict(fields)
    if "password" in fields:
        fields["password"] = generate_password_hash(fields["password"])
    with unit_of_work() as conn, integrity_guard():
        if users.update(conn, user_id, fields) == 0:
            raise NotFoundError("User not found")
        return users.get(conn, user_id)


def delete(user_id: str) -> None:
    with unit_of_work() as conn, integrity_guard():
        if users.delete(conn, user_id) == 0:
            raise NotFoundError("User not found")
