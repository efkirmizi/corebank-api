"""Unit tests for the transfer service using fake repositories — no database.

These pass because the service imports no Flask and reaches the database only
through injectable repository functions and the unit of work. That is the
practical payoff of the layering.
"""

from __future__ import annotations

import contextlib
from decimal import Decimal

import pytest

from app.services import transaction_service as svc
from app.services.exceptions import BusinessRuleError, ForbiddenError, NotFoundError

ADMIN = {"user_id": "admin", "role": "ADMIN", "customer_id": None}
ALICE = {"user_id": "u1", "role": "USER", "customer_id": "c1"}
BOB = {"user_id": "u2", "role": "USER", "customer_id": "c2"}


class FakeAccounts:
    def __init__(self, accounts):
        self.accounts = accounts

    def lock(self, conn, account_id):
        a = self.accounts.get(account_id)
        return {**a, "account_id": account_id} if a else None

    def debit(self, conn, account_id, amount):
        a = self.accounts[account_id]
        if a["balance"] >= amount:
            a["balance"] -= amount
            return 1
        return 0

    def credit(self, conn, account_id, amount):
        self.accounts[account_id]["balance"] += amount
        return 1


class FakeTransactions:
    def __init__(self):
        self.inserted = []

    def insert(self, conn, record):
        self.inserted.append(record)


@pytest.fixture()
def ledger(monkeypatch):
    accounts = {
        "A": {"customer_id": "c1", "balance": Decimal("100.00")},
        "B": {"customer_id": "c2", "balance": Decimal("50.00")},
    }
    fake_accounts = FakeAccounts(accounts)
    fake_txns = FakeTransactions()

    @contextlib.contextmanager
    def fake_uow():
        yield object()

    monkeypatch.setattr(svc, "accounts", fake_accounts)
    monkeypatch.setattr(svc, "transactions", fake_txns)
    monkeypatch.setattr(svc, "unit_of_work", fake_uow)
    return accounts, fake_txns


def test_happy_path_moves_money_and_records(ledger):
    accounts, txns = ledger
    result = svc.transfer(ADMIN, "A", "B", Decimal("30"))
    assert accounts["A"]["balance"] == Decimal("70.00")
    assert accounts["B"]["balance"] == Decimal("80.00")
    assert accounts["A"]["balance"] + accounts["B"]["balance"] == Decimal("150.00")
    assert result["transaction_type"] == "TRANSFER"
    assert txns.inserted and txns.inserted[0]["amount"] == Decimal("30.00")


def test_insufficient_funds_declined_without_mutation(ledger):
    accounts, txns = ledger
    with pytest.raises(BusinessRuleError, match="Insufficient funds"):
        svc.transfer(ADMIN, "A", "B", Decimal("1000"))
    assert accounts["A"]["balance"] == Decimal("100.00")
    assert accounts["B"]["balance"] == Decimal("50.00")
    assert txns.inserted == []


def test_self_transfer_rejected(ledger):
    with pytest.raises(BusinessRuleError, match="must differ"):
        svc.transfer(ADMIN, "A", "A", Decimal("10"))


@pytest.mark.parametrize("amount", ["0", "-5"])
def test_non_positive_amount_rejected(ledger, amount):
    with pytest.raises(BusinessRuleError, match="greater than zero"):
        svc.transfer(ADMIN, "A", "B", Decimal(amount))


def test_customer_cannot_send_from_others_account(ledger):
    accounts, _ = ledger
    with pytest.raises(ForbiddenError):
        svc.transfer(BOB, "A", "B", Decimal("10"))  # A belongs to c1, not Bob
    assert accounts["A"]["balance"] == Decimal("100.00")


def test_owner_can_send_from_own_account(ledger):
    accounts, _ = ledger
    svc.transfer(ALICE, "A", "B", Decimal("10"))
    assert accounts["A"]["balance"] == Decimal("90.00")


def test_missing_account_raises_not_found(ledger):
    with pytest.raises(NotFoundError):
        svc.transfer(ADMIN, "A", "Z", Decimal("10"))
