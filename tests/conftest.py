"""Shared test fixtures.

The integration and concurrency suites run against a real MySQL database — SQL
typos and schema drift should fail a test, not hide behind a mock. Connection
details come from the environment (with local defaults), so the same tests run
in CI against a service container. The test database is dropped and rebuilt from
migrations + seeds at the start of each session for a clean, repeatable slate.
"""

from __future__ import annotations

import os

# Must be set before importing app.config, which reads the environment at import.
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_PORT", "3307")
os.environ.setdefault("DB_USER", "root")
os.environ.setdefault("DB_PASSWORD", "devpassword")
os.environ.setdefault("DB_NAME", "bank_test")
os.environ.setdefault("DB_POOL_SIZE", "10")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-at-least-32-bytes-long-000")

import pymysql  # noqa: E402
import pytest  # noqa: E402

from app import create_app  # noqa: E402
from app.db.pool import init_pool, reset_pool  # noqa: E402
from scripts import migrate as migrate_mod  # noqa: E402

# Seed identifiers reused across tests.
ALICE_CUSTOMER = "a0000000-0000-0000-0000-0000000000c1"
BOB_CUSTOMER = "a0000000-0000-0000-0000-0000000000c2"
ALICE_CHECKING = "acc00000-0000-0000-0000-000000000001"
ALICE_SAVINGS = "acc00000-0000-0000-0000-000000000002"
BOB_CHECKING = "acc00000-0000-0000-0000-000000000003"
DOWNTOWN_BRANCH = "11111111-1111-1111-1111-111111111111"


def _drop_and_rebuild() -> None:
    conn = pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        autocommit=True,
    )
    with conn.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS `{os.environ['DB_NAME']}`")
    conn.close()
    migrate_mod.run_migrations()
    migrate_mod.load_seeds()


@pytest.fixture(scope="session")
def app():
    _drop_and_rebuild()
    application = create_app("testing")
    reset_pool()
    init_pool(application.config)
    yield application
    reset_pool()


@pytest.fixture()
def client(app):
    return app.test_client()


def _token(client, username, password):
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.get_json()
    return resp.get_json()["access_token"]


@pytest.fixture()
def admin_headers(client):
    return {"Authorization": f"Bearer {_token(client, 'admin', 'admin123')}"}


@pytest.fixture()
def alice_headers(client):
    return {"Authorization": f"Bearer {_token(client, 'alice', 'alice123')}"}


@pytest.fixture()
def bob_headers(client):
    return {"Authorization": f"Bearer {_token(client, 'bob', 'bob123')}"}
