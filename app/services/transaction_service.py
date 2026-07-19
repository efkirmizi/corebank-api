"""Transactions and the money-transfer flow.

``transfer`` is the safety centerpiece. The original implementation issued two
bare UPDATEs with no transaction, no locking, and no rollback: if the second
failed, money vanished, and concurrent transfers could overdraw an account.
Here the whole movement runs inside one unit of work:

  1. lock both accounts FOR UPDATE, ordered by id so opposing transfers cannot
     deadlock;
  2. debit the sender with a SQL-guarded UPDATE that refuses to go negative;
  3. credit the receiver and record the ledger row;
  4. commit — or roll the entire thing back on any error.
"""

from __future__ import annotations

from decimal import Decimal

from app.db import read_only, unit_of_work
from app.repositories import accounts, transactions

from ._helpers import ensure_owner_or_admin, new_id, utcnow
from .exceptions import BusinessRuleError, ForbiddenError, NotFoundError


def transfer(actor: dict, sender_id: str, receiver_id: str, amount: Decimal) -> dict:
    amount = Decimal(amount).quantize(Decimal("0.01"))
    if amount <= 0:
        raise BusinessRuleError("Transfer amount must be greater than zero")
    if sender_id == receiver_id:
        raise BusinessRuleError("Sender and receiver accounts must differ")

    with unit_of_work() as conn:
        # Lock in a deterministic order to avoid deadlock between A->B and B->A.
        first, second = sorted((sender_id, receiver_id))
        locked = {first: accounts.lock(conn, first), second: accounts.lock(conn, second)}
        sender = locked[sender_id]
        receiver = locked[receiver_id]

        if sender is None:
            raise NotFoundError("Sender account not found")
        if receiver is None:
            raise NotFoundError("Receiver account not found")

        if actor.get("role") != "ADMIN" and actor.get("customer_id") != sender["customer_id"]:
            raise ForbiddenError("You may only transfer from your own account")

        # Overdraft protection lives in the WHERE clause: 0 rows means declined.
        if accounts.debit(conn, sender_id, amount) != 1:
            raise BusinessRuleError("Insufficient funds")
        accounts.credit(conn, receiver_id, amount)

        record = {
            "transaction_id": new_id(),
            "from_account_id": sender_id,
            "to_account_id": receiver_id,
            "transaction_type": "TRANSFER",
            "amount": amount,
            "transaction_timestamp": utcnow(),
        }
        transactions.insert(conn, record)

    return record


def list_all() -> list[dict]:
    with read_only() as conn:
        return transactions.list_all(conn)


def get(transaction_id: str, actor: dict) -> dict:
    with read_only() as conn:
        txn = transactions.get(conn, transaction_id)
        if txn is None:
            raise NotFoundError("Transaction not found")
        _ensure_actor_sees_transaction(conn, actor, txn)
        return txn


def list_by_account(account_id: str, actor: dict) -> list[dict]:
    with read_only() as conn:
        account = accounts.get(conn, account_id)
        if account is None:
            raise NotFoundError("Account not found")
        ensure_owner_or_admin(actor, account["customer_id"])
        return transactions.list_by_account(conn, account_id)


def delete(transaction_id: str) -> None:
    with unit_of_work() as conn:
        if transactions.delete(conn, transaction_id) == 0:
            raise NotFoundError("Transaction not found")


def high_transactions(minimum) -> list[dict]:
    with read_only() as conn:
        return transactions.customers_with_high_transactions(conn, minimum)


def _ensure_actor_sees_transaction(conn, actor: dict, txn: dict) -> None:
    if actor.get("role") == "ADMIN":
        return
    for acct_id in (txn["from_account_id"], txn["to_account_id"]):
        if acct_id:
            account = accounts.get(conn, acct_id)
            if account and account["customer_id"] == actor.get("customer_id"):
                return
    raise ForbiddenError("You do not have access to this transaction")
