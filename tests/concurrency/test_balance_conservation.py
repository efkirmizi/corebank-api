"""The safety centerpiece: money is conserved under concurrent transfers.

Many threads fire random transfers among a shared set of accounts. Because each
transfer runs in one unit of work — both accounts locked FOR UPDATE in id order,
the debit guarded in SQL — the invariants must hold no matter how operations
interleave:

  * the total balance across all accounts never changes;
  * no account ever goes negative;
  * overdrafts are rejected cleanly as business errors, never as database errors.

The naive check-then-act implementation lets concurrent overdrafts slip past the
application check and reach the database, where only the CHECK constraint stops
them — surfacing as HTTP 500s. See scripts/concurrency_demo.py for that contrast.
"""
from __future__ import annotations

import random
import threading
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest

from app.db import read_only, unit_of_work
from app.repositories import accounts as accounts_repo
from app.repositories import branches as branches_repo
from app.repositories import customers as customers_repo
from app.repositories import transactions as transactions_repo
from app.services import account_service, branch_service, customer_service, transaction_service
from app.services.exceptions import BusinessRuleError

pytestmark = [pytest.mark.integration, pytest.mark.concurrency]

ADMIN = {"user_id": "admin", "role": "ADMIN", "customer_id": None}
N_ACCOUNTS = 5
START = Decimal("1000.00")
N_THREADS = 8
TRANSFERS_PER_THREAD = 25


@pytest.fixture()
def arena(app):
    """Create an isolated branch, customer, and funded accounts; tear them down."""
    branch = branch_service.create(
        {
            "branch_name": f"Arena {random.randint(0, 1_000_000)}",
            "address_line1": "1 Arena St",
            "city": "Testville",
            "zip_code": "00000",
            "phone_number": str(random.randint(10**10, 10**11)),
        }
    )
    customer = customer_service.create(
        {
            "first_name": "Arena",
            "last_name": "Customer",
            "date_of_birth": "1990-01-01",
            "phone_number": str(random.randint(10**10, 10**11)),
            "email": f"arena{random.randint(0, 1_000_000)}@example.com",
            "address_line1": "1 Arena St",
            "city": "Testville",
            "zip_code": "00000",
        }
    )
    account_ids = []
    for _ in range(N_ACCOUNTS):
        acct = account_service.create(customer["customer_id"], "CHECKING", branch["branch_id"])
        account_service.set_balance(acct["account_id"], START)
        account_ids.append(acct["account_id"])

    yield account_ids

    # Teardown: remove created transactions, then accounts, customer, branch.
    txn_ids: set[str] = set()
    with read_only() as conn:
        for acct_id in account_ids:
            for txn in transactions_repo.list_by_account(conn, acct_id):
                txn_ids.add(txn["transaction_id"])
    with unit_of_work() as conn:
        for tid in txn_ids:
            transactions_repo.delete(conn, tid)
        for acct_id in account_ids:
            accounts_repo.delete(conn, acct_id)
        customers_repo.delete(conn, customer["customer_id"])
        branches_repo.delete(conn, branch["branch_id"])


def _total_balance(account_ids) -> Decimal:
    with read_only() as conn:
        return sum((accounts_repo.get(conn, a)["balance"] for a in account_ids), Decimal("0.00"))


def test_total_balance_is_conserved_under_concurrency(arena):
    account_ids = arena
    assert _total_balance(account_ids) == START * N_ACCOUNTS

    barrier = threading.Barrier(N_THREADS)

    def worker(seed: int) -> None:
        rng = random.Random(seed)
        barrier.wait()  # release all threads together to maximize contention
        for _ in range(TRANSFERS_PER_THREAD):
            sender, receiver = rng.sample(account_ids, 2)
            amount = Decimal(rng.randint(1, 50))
            try:
                transaction_service.transfer(ADMIN, sender, receiver, amount)
            except BusinessRuleError:
                pass  # insufficient funds is a valid, expected outcome

    with ThreadPoolExecutor(max_workers=N_THREADS) as pool:
        list(pool.map(worker, range(N_THREADS)))

    # Invariant 1: total conserved to the cent.
    assert _total_balance(account_ids) == START * N_ACCOUNTS

    # Invariant 2: no account went negative.
    with read_only() as conn:
        balances = [accounts_repo.get(conn, a)["balance"] for a in account_ids]
    assert all(b >= 0 for b in balances), balances
