"""Demonstrate why the atomic transfer matters.

Many threads hammer a single account with concurrent withdrawals:

  1. NAIVE — the original approach: read the balance, check it in Python, then
     issue an unlocked UPDATE. No row lock. The check races, so multiple
     requests read the same sufficient balance and all proceed to debit.
  2. ATOMIC — the service the API uses: one unit of work, the row locked
     FOR UPDATE, the debit guarded in SQL (WHERE balance >= amount).

Both conserve the total (the UPDATEs are relative and a CHECK constraint forbids
negative balances). The difference is robustness: under the naive version the
overdrafts that slip past the Python check are stopped only by the database's
CHECK constraint, surfacing as OperationalErrors — HTTP 500s in the old app.
The atomic version rejects every overdraft cleanly as a business error (HTTP 422)
and never lets one reach the database. Run it yourself:

    python -m scripts.concurrency_demo

Requires the same DB_* environment variables as the app.
"""

from __future__ import annotations

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pymysql

from app.db import get_connection, read_only, unit_of_work
from app.db.pool import init_pool
from app.repositories import accounts as accounts_repo
from app.repositories import branches as branches_repo
from app.repositories import customers as customers_repo
from app.repositories import transactions as transactions_repo
from app.services import account_service, branch_service, customer_service, transaction_service
from app.services.exceptions import BusinessRuleError

ADMIN = {"user_id": "admin", "role": "ADMIN", "customer_id": None}
N_ACCOUNTS = 4
START = Decimal("100.00")
N_THREADS = 8
TRANSFERS = 60


def _config() -> dict:
    return {
        "DB_HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "DB_PORT": int(os.getenv("DB_PORT", "3307")),
        "DB_USER": os.getenv("DB_USER", "root"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD", "devpassword"),
        "DB_NAME": os.getenv("DB_NAME", "bank"),
        "DB_POOL_SIZE": 12,
    }


def naive_transfer(sender: str, receiver: str, amount: Decimal) -> None:
    """The unsafe original: check-then-act with a visible race window."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT balance FROM account WHERE account_id = %s", (sender,))
            balance = cur.fetchone()["balance"]
        if balance < amount:
            raise BusinessRuleError("Insufficient funds")  # the app's intended 422
        time.sleep(0.001)  # widen the check-then-act gap so the race is visible
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE account SET balance = balance - %s WHERE account_id = %s", (amount, sender)
            )
            conn.commit()
            cur.execute(
                "UPDATE account SET balance = balance + %s WHERE account_id = %s",
                (amount, receiver),
            )
            conn.commit()
    finally:
        conn.close()


def _storm(transfer_fn, account_ids) -> dict:
    counters = {"ok": 0, "clean_reject": 0, "db_error": 0}
    lock = threading.Lock()

    def worker(seed: int) -> None:
        import random

        rng = random.Random(seed)
        local = {"ok": 0, "clean_reject": 0, "db_error": 0}
        for _ in range(TRANSFERS):
            sender = account_ids[0]  # concentrate contention on one account
            receiver = rng.choice(account_ids[1:])
            amount = Decimal(rng.randint(1, 20))
            try:
                transfer_fn(sender, receiver, amount)
                local["ok"] += 1
            except BusinessRuleError:
                local["clean_reject"] += 1  # atomic path: graceful 422
            except pymysql.err.OperationalError:
                local["db_error"] += 1  # naive path: overdraft only caught by the DB
        with lock:
            for key in counters:
                counters[key] += local[key]

    with ThreadPoolExecutor(max_workers=N_THREADS) as pool:
        list(pool.map(worker, range(N_THREADS)))
    return counters


def _reset(account_ids) -> None:
    with unit_of_work() as conn:
        for a in account_ids:
            accounts_repo.set_balance(conn, a, START)


def _report(label: str, account_ids, counters: dict) -> None:
    with read_only() as conn:
        balances = [accounts_repo.get(conn, a)["balance"] for a in account_ids]
    total = sum(balances, Decimal("0.00"))
    expected = START * N_ACCOUNTS
    print(f"\n{label}")
    print(f"  transfers ok        : {counters['ok']}")
    print(f"  cleanly rejected 422: {counters['clean_reject']}")
    print(f"  DB errors (would 500): {counters['db_error']}")
    print(f"  total balance       : {total}  (expected {expected}, conserved={total == expected})")


def main() -> None:
    init_pool(_config())
    branch = branch_service.create(
        {
            "branch_name": f"Demo {time.time_ns()}",
            "address_line1": "1 Demo St",
            "city": "Testville",
            "zip_code": "00000",
            "phone_number": str(time.time_ns())[:12],
        }
    )
    customer = customer_service.create(
        {
            "first_name": "Demo",
            "last_name": "User",
            "date_of_birth": "1990-01-01",
            "phone_number": str(time.time_ns())[:11],
            "email": f"demo{time.time_ns()}@example.com",
            "address_line1": "1 Demo St",
            "city": "Testville",
            "zip_code": "00000",
        }
    )
    account_ids = []
    for _ in range(N_ACCOUNTS):
        acct = account_service.create(customer["customer_id"], "CHECKING", branch["branch_id"])
        account_service.set_balance(acct["account_id"], START)
        account_ids.append(acct["account_id"])

    try:
        _reset(account_ids)
        naive_counts = _storm(naive_transfer, account_ids)
        _report("NAIVE  (check-then-act, no row lock)", account_ids, naive_counts)

        _reset(account_ids)
        atomic_counts = _storm(
            lambda s, r, a: transaction_service.transfer(ADMIN, s, r, a), account_ids
        )
        _report("ATOMIC (unit of work, FOR UPDATE, guarded debit)", account_ids, atomic_counts)

        print(
            "\nTakeaway: the atomic path turned "
            f"{naive_counts['db_error']} database errors into "
            f"{atomic_counts['clean_reject']} clean rejections — zero reached the DB."
        )
    finally:
        _cleanup(account_ids, customer["customer_id"], branch["branch_id"])


def _cleanup(account_ids, customer_id, branch_id) -> None:
    txn_ids = set()
    with read_only() as conn:
        for a in account_ids:
            for t in transactions_repo.list_by_account(conn, a):
                txn_ids.add(t["transaction_id"])
    with unit_of_work() as conn:
        for t in txn_ids:
            transactions_repo.delete(conn, t)
        for a in account_ids:
            accounts_repo.delete(conn, a)
        customers_repo.delete(conn, customer_id)
        branches_repo.delete(conn, branch_id)


if __name__ == "__main__":
    main()
