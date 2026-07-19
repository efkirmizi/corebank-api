"""The unit of work commits on success and rolls back on any exception."""

from __future__ import annotations

import pytest

from app.db import read_only, unit_of_work
from app.repositories import branches

pytestmark = pytest.mark.integration


def _branch(bid: str, name: str) -> dict:
    return {
        "branch_id": bid,
        "branch_name": name,
        "address_line1": "1 Test St",
        "address_line2": None,
        "city": "Testville",
        "zip_code": "00000",
        "phone_number": name[:14],
    }


def test_commit_persists(app):
    bid = "uow-commit-branch-01"
    with unit_of_work() as conn:
        branches.insert(conn, _branch(bid, "UoWCommit"))
    with read_only() as conn:
        assert branches.get(conn, bid) is not None
    with unit_of_work() as conn:  # cleanup
        branches.delete(conn, bid)


def test_rollback_on_exception(app):
    bid = "uow-rollback-branch-1"
    with pytest.raises(RuntimeError):
        with unit_of_work() as conn:
            branches.insert(conn, _branch(bid, "UoWRollback"))
            raise RuntimeError("boom after insert")
    with read_only() as conn:
        assert branches.get(conn, bid) is None, "insert was not rolled back"
