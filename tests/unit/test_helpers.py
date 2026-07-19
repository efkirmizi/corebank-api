"""Unit tests for the Flask-free service helpers."""

from __future__ import annotations

import pymysql
import pytest

from app.services._helpers import ensure_owner_or_admin, integrity_guard
from app.services.exceptions import (
    BadRequestError,
    BusinessRuleError,
    ConflictError,
    ForbiddenError,
)

ADMIN = {"role": "ADMIN", "customer_id": None}
ALICE = {"role": "USER", "customer_id": "c1"}


def test_admin_passes_any_owner_check():
    ensure_owner_or_admin(ADMIN, "any-customer")  # no raise


def test_owner_passes_own_check():
    ensure_owner_or_admin(ALICE, "c1")  # no raise


def test_non_owner_is_forbidden():
    with pytest.raises(ForbiddenError):
        ensure_owner_or_admin(ALICE, "c2")


def test_missing_customer_is_forbidden_for_non_admin():
    with pytest.raises(ForbiddenError):
        ensure_owner_or_admin(ALICE, None)


def _integrity_error(errno):
    return pymysql.err.IntegrityError(errno, "simulated")


def test_duplicate_maps_to_conflict():
    with pytest.raises(ConflictError):
        with integrity_guard():
            raise _integrity_error(1062)


def test_missing_fk_maps_to_bad_request():
    with pytest.raises(BadRequestError):
        with integrity_guard():
            raise _integrity_error(1452)


def test_referenced_delete_maps_to_conflict():
    with pytest.raises(ConflictError):
        with integrity_guard():
            raise _integrity_error(1451)


def test_check_constraint_maps_to_business_rule():
    with pytest.raises(BusinessRuleError):
        with integrity_guard():
            raise _integrity_error(3819)


def test_unknown_integrity_error_reraised():
    with pytest.raises(pymysql.err.IntegrityError):
        with integrity_guard():
            raise _integrity_error(9999)
