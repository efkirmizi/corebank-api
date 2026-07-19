"""One admin flow that creates, reads, mutates, and deletes every resource.

Besides proving each endpoint works end to end, this exercises the CRUD service
paths (create/get/update/status/delete) that the focused flow tests do not.
Entities are created in dependency order and removed in reverse, so the database
is left as it was found.
"""

from __future__ import annotations

import random
import uuid

import pytest

from tests.conftest import DOWNTOWN_BRANCH

pytestmark = pytest.mark.integration


def _digits(n: int) -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(n))


def test_full_resource_lifecycle(client, admin_headers):
    h = admin_headers
    created: list[tuple[str, str]] = []  # (url, id) for teardown in reverse

    def post(url, body, id_field):
        resp = client.post(url, headers=h, json=body)
        assert resp.status_code == 201, (url, resp.status_code, resp.get_json())
        rid = resp.get_json()[id_field]
        created.append((url.rstrip("/"), rid))
        return rid

    try:
        # customer
        customer_id = post(
            "/api/v1/customers/",
            {
                "first_name": "Crud",
                "last_name": "Flow",
                "date_of_birth": "1991-02-03",
                "phone_number": _digits(11),
                "email": f"crud{uuid.uuid4().hex[:8]}@example.com",
                "address_line1": "1 Flow St",
                "city": "Testville",
                "zip_code": "10101",
            },
            "customer_id",
        )

        # employee
        employee_id = post(
            "/api/v1/employees/",
            {
                "branch_id": DOWNTOWN_BRANCH,
                "first_name": "Emp",
                "last_name": "Loyee",
                "position": "Teller",
                "hire_date": "2023-01-01T09:00:00",
                "phone_number": _digits(11),
                "email": f"emp{uuid.uuid4().hex[:8]}@example.com",
            },
            "employee_id",
        )

        # account
        account_id = post(
            "/api/v1/accounts/",
            {"customer_id": customer_id, "account_type": "CHECKING", "branch_id": DOWNTOWN_BRANCH},
            "account_id",
        )

        # card (on the account) — status update exercised
        card_id = post(
            "/api/v1/cards/",
            {
                "account_id": account_id,
                "card_type": "DEBIT",
                "card_number": _digits(16),
                "expiration_date": "2030-01-31",
                "cvv": _digits(3),
            },
            "card_id",
        )
        blocked = client.put(
            f"/api/v1/cards/{card_id}/status", headers=h, json={"status": "BLOCKED"}
        )
        assert blocked.status_code == 200 and blocked.get_json()["status"] == "BLOCKED"
        assert blocked.get_json()["card_number"].startswith("************")  # masked

        # loan + payment
        loan_id = post(
            "/api/v1/loans/",
            {
                "customer_id": customer_id,
                "loan_type": "PERSONAL",
                "principal_amount": "10000.00",
                "interest_rate": "5.50",
                "start_date": "2024-01-01",
                "end_date": "2029-01-01",
            },
            "loan_id",
        )
        status_resp = client.put(
            f"/api/v1/loans/{loan_id}/status", headers=h, json={"status": "PAID_OFF"}
        )
        assert status_resp.status_code == 200 and status_resp.get_json()["status"] == "PAID_OFF"

        post(  # registered for teardown; id not needed here
            "/api/v1/loan-payments/",
            {"loan_id": loan_id, "payment_amount": "500.00", "remaining_balance": "9500.00"},
            "loan_payment_id",
        )
        by_loan = client.get(f"/api/v1/loan-payments/by-loan/{loan_id}", headers=h)
        assert by_loan.status_code == 200 and len(by_loan.get_json()) == 1

        # credit score (update exercised)
        score_id = post(
            "/api/v1/credit-scores/",
            {"customer_id": customer_id, "score": "700.00", "risk_category": "LOW"},
            "credit_score_id",
        )
        upd = client.put(f"/api/v1/credit-scores/{score_id}", headers=h, json={"score": "710.00"})
        assert upd.status_code == 200 and upd.get_json()["score"] == "710.00"

        # support ticket (status update exercised)
        ticket_id = post(
            "/api/v1/support-tickets/",
            {
                "customer_id": customer_id,
                "employee_id": employee_id,
                "issue_description": "Test issue",
            },
            "ticket_id",
        )
        resolved = client.put(
            f"/api/v1/support-tickets/{ticket_id}/status", headers=h, json={"status": "RESOLVED"}
        )
        assert resolved.status_code == 200 and resolved.get_json()["status"] == "RESOLVED"

        # user (update exercised)
        user_id = post(
            "/api/v1/users/",
            {
                "username": f"user{uuid.uuid4().hex[:8]}",
                "password": "secret123",
                "role": "USER",
                "customer_id": customer_id,
            },
            "user_id",
        )
        renamed = client.put(f"/api/v1/users/{user_id}", headers=h, json={"role": "ADMIN"})
        assert renamed.status_code == 200 and renamed.get_json()["role"] == "ADMIN"

        # every created entity is fetchable
        for url, rid in created:
            got = client.get(f"{url}/{rid}", headers=h)
            assert got.status_code == 200, (url, rid, got.status_code)

    finally:
        # delete in reverse dependency order
        for url, rid in reversed(created):
            resp = client.delete(f"{url}/{rid}", headers=h)
            assert resp.status_code in (204, 404), (url, rid, resp.status_code)
