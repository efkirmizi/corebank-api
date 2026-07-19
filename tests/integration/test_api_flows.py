"""End-to-end HTTP flows through the app against a real MySQL database."""
from __future__ import annotations

import uuid

import pytest

from tests.conftest import (
    ALICE_CHECKING,
    ALICE_SAVINGS,
    BOB_CHECKING,
    DOWNTOWN_BRANCH,
)

pytestmark = pytest.mark.integration


# --- authentication ---------------------------------------------------------


def test_login_returns_token(client):
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    assert resp.get_json()["access_token"]


def test_login_bad_password_is_401(client):
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "nope"})
    assert resp.status_code == 401


def test_me_reports_identity(client, alice_headers):
    resp = client.get("/api/v1/auth/me", headers=alice_headers)
    assert resp.status_code == 200
    assert resp.get_json()["role"] == "USER"


# --- authorization ----------------------------------------------------------


def test_missing_token_is_401(client):
    assert client.get("/api/v1/accounts/").status_code == 401


def test_customer_cannot_list_customers(client, alice_headers):
    assert client.get("/api/v1/customers/", headers=alice_headers).status_code == 403


def test_customer_sees_only_own_accounts(client, alice_headers, admin_headers):
    alice_accounts = client.get("/api/v1/accounts/", headers=alice_headers).get_json()
    all_accounts = client.get("/api/v1/accounts/", headers=admin_headers).get_json()
    assert len(alice_accounts) == 2
    assert len(all_accounts) == 4
    assert {a["customer_id"] for a in alice_accounts} == {alice_accounts[0]["customer_id"]}


def test_customer_cannot_read_foreign_account(client, bob_headers):
    # Bob tries to read Alice's account.
    assert client.get(f"/api/v1/accounts/{ALICE_CHECKING}", headers=bob_headers).status_code == 403


def test_create_user_is_admin_only(client, alice_headers):
    resp = client.post(
        "/api/v1/users/",
        headers=alice_headers,
        json={"username": "intruder", "password": "hunter2", "role": "ADMIN"},
    )
    assert resp.status_code == 403


# --- money transfer ---------------------------------------------------------


def _balance(client, headers, account_id):
    from decimal import Decimal

    body = client.get(f"/api/v1/accounts/{account_id}", headers=headers).get_json()
    return Decimal(body["balance"])


def test_transfer_moves_money_and_conserves(client, alice_headers):
    from decimal import Decimal

    amount = Decimal("125.50")
    before_from = _balance(client, alice_headers, ALICE_CHECKING)
    before_to = _balance(client, alice_headers, ALICE_SAVINGS)

    resp = client.post(
        "/api/v1/transactions/transfer",
        headers=alice_headers,
        json={
            "sender_account_id": ALICE_CHECKING,
            "receiver_account_id": ALICE_SAVINGS,
            "amount": str(amount),
        },
    )
    assert resp.status_code == 201

    after_from = _balance(client, alice_headers, ALICE_CHECKING)
    after_to = _balance(client, alice_headers, ALICE_SAVINGS)
    assert after_from == before_from - amount
    assert after_to == before_to + amount
    assert after_from + after_to == before_from + before_to

    # restore
    client.post(
        "/api/v1/transactions/transfer",
        headers=alice_headers,
        json={
            "sender_account_id": ALICE_SAVINGS,
            "receiver_account_id": ALICE_CHECKING,
            "amount": "125.50",
        },
    )


def test_overdraft_rejected(client, alice_headers):
    resp = client.post(
        "/api/v1/transactions/transfer",
        headers=alice_headers,
        json={
            "sender_account_id": ALICE_CHECKING,
            "receiver_account_id": ALICE_SAVINGS,
            "amount": "9999999.00",
        },
    )
    assert resp.status_code == 422
    assert "Insufficient" in resp.get_json()["message"]


def test_self_transfer_rejected(client, alice_headers):
    resp = client.post(
        "/api/v1/transactions/transfer",
        headers=alice_headers,
        json={
            "sender_account_id": ALICE_CHECKING,
            "receiver_account_id": ALICE_CHECKING,
            "amount": "1.00",
        },
    )
    assert resp.status_code == 422


def test_transfer_from_foreign_account_forbidden(client, bob_headers):
    resp = client.post(
        "/api/v1/transactions/transfer",
        headers=bob_headers,
        json={
            "sender_account_id": ALICE_CHECKING,
            "receiver_account_id": BOB_CHECKING,
            "amount": "1.00",
        },
    )
    assert resp.status_code == 403


def test_transfer_validation_error_lists_fields(client, alice_headers):
    resp = client.post("/api/v1/transactions/transfer", headers=alice_headers, json={"amount": "x"})
    assert resp.status_code == 422
    errors = resp.get_json()["errors"]["json"]
    assert "sender_account_id" in errors and "amount" in errors


# --- admin CRUD round trip --------------------------------------------------


def test_branch_crud_round_trip(client, admin_headers):
    created = client.post(
        "/api/v1/branches/",
        headers=admin_headers,
        json={
            "branch_name": f"Branch {uuid.uuid4().hex[:8]}",
            "address_line1": "9 New Rd",
            "city": "Gotham",
            "zip_code": "22222",
            "phone_number": str(uuid.uuid4().int)[:12],
        },
    )
    assert created.status_code == 201
    branch_id = created.get_json()["branch_id"]

    assert client.get(f"/api/v1/branches/{branch_id}", headers=admin_headers).status_code == 200

    updated = client.put(
        f"/api/v1/branches/{branch_id}", headers=admin_headers, json={"city": "Metropolis"}
    )
    assert updated.status_code == 200 and updated.get_json()["city"] == "Metropolis"

    assert client.delete(f"/api/v1/branches/{branch_id}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/v1/branches/{branch_id}", headers=admin_headers).status_code == 404


def test_unknown_resource_is_404(client, admin_headers):
    assert client.get("/api/v1/branches/does-not-exist", headers=admin_headers).status_code == 404


# --- analytical reports -----------------------------------------------------


def test_branch_conditions_report(client, admin_headers):
    resp = client.get("/api/v1/branches/reports/conditions", headers=admin_headers)
    assert resp.status_code == 200
    names = [b["branch_name"] for b in resp.get_json()]
    assert "Downtown Branch" in names


def test_high_value_report(client, admin_headers):
    resp = client.get("/api/v1/transactions/reports/high-value/10000", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()[0]["first_name"] == "Carol"


def test_top_resolvers_report(client, admin_headers):
    resp = client.get("/api/v1/support-tickets/reports/top-resolvers", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()[0]["resolved_tickets"] == 2


def test_openapi_document_served(client):
    spec = client.get("/openapi.json").get_json()
    assert spec["info"]["title"] == "corebank-api"
    assert "/api/v1/transactions/transfer" in spec["paths"]


# --- health -----------------------------------------------------------------


def test_health_and_readiness(client):
    assert client.get("/health").status_code == 200
    assert client.get("/health/ready").status_code == 200
