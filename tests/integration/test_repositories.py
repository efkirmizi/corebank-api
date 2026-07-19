"""Repositories against a real MySQL database.

These catch what fake repositories cannot: SQL typos, column drift, and the
driver returning DECIMAL money as Decimal rather than float.
"""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest

from app.db import read_only, unit_of_work
from app.repositories import accounts, branches, customers, support_tickets, transactions
from tests.conftest import ALICE_CHECKING

pytestmark = pytest.mark.integration


def _customer(cid: str) -> dict:
    tag = uuid.uuid4().hex[:8]
    return {
        "customer_id": cid,
        "first_name": "Repo",
        "last_name": "Test",
        "date_of_birth": date(1990, 1, 1),
        "phone_number": tag,
        "email": f"{tag}@example.com",
        "address_line1": "1 Repo St",
        "address_line2": None,
        "city": "Testville",
        "zip_code": "00000",
        "wage_declaration": Decimal("50000.00"),
    }


def test_customer_crud_round_trip(app):
    cid = f"repo-{uuid.uuid4()}"[:36]
    with unit_of_work() as conn:
        customers.insert(conn, _customer(cid))

    with read_only() as conn:
        fetched = customers.get(conn, cid)
    assert fetched is not None
    assert fetched["first_name"] == "Repo"
    assert isinstance(fetched["wage_declaration"], Decimal)

    with unit_of_work() as conn:
        changed = customers.update(conn, cid, {"city": "Newcity"})
    assert changed == 1

    with unit_of_work() as conn:
        assert customers.delete(conn, cid) == 1
    with read_only() as conn:
        assert customers.get(conn, cid) is None


def test_account_balance_is_decimal(app):
    with read_only() as conn:
        account = accounts.get(conn, ALICE_CHECKING)
    assert isinstance(account["balance"], Decimal)


def test_analytical_queries_return_seed_rows(app):
    with read_only() as conn:
        conditions = branches.with_conditions(conn, 5, 3)
        high = transactions.customers_with_high_transactions(conn, 10000)
        resolvers = support_tickets.top_resolvers(conn)

    assert any(b["branch_name"] == "Downtown Branch" for b in conditions)
    assert high[0]["first_name"] == "Carol"
    assert isinstance(high[0]["total_transaction"], Decimal)
    assert resolvers[0]["resolved_tickets"] == 2
