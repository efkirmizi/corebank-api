"""Small cross-service helpers: ids, timestamps, authorization, DB-error mapping.

All Flask-free, so services remain unit-testable without an app context.
"""
from __future__ import annotations

import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

import pymysql

from .exceptions import (
    BadRequestError,
    BusinessRuleError,
    ConflictError,
    ForbiddenError,
)

ADMIN = "ADMIN"


def new_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    """Naive UTC timestamp suitable for a MySQL DATETIME column."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def ensure_owner_or_admin(actor: dict, customer_id: str | None) -> None:
    """Admins pass; otherwise the actor must own the resource's customer_id."""
    if actor.get("role") == ADMIN:
        return
    if not customer_id or actor.get("customer_id") != customer_id:
        raise ForbiddenError("You do not have access to this resource")


@contextmanager
def integrity_guard():
    """Translate MySQL integrity errors into domain exceptions."""
    try:
        yield
    except pymysql.err.IntegrityError as exc:
        errno = exc.args[0] if exc.args else None
        if errno == 1062:
            raise ConflictError("A record with these unique values already exists") from exc
        if errno == 1452:
            raise BadRequestError("A referenced record does not exist") from exc
        if errno == 1451:
            raise ConflictError(
                "Cannot delete: this record is still referenced by others"
            ) from exc
        if errno in (3819, 4025):  # CHECK constraint violated
            raise BusinessRuleError("A database constraint was violated") from exc
        raise
