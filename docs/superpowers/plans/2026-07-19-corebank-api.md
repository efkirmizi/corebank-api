# corebank-api Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan phase-by-phase. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure a course-project Flask/MySQL banking API into a layered, containerized, tested, portfolio-grade service without replacing its hand-written SQL.

**Architecture:** `api → services → repositories → db`, dependencies inward only. Services own transaction boundaries via a unit-of-work context manager; repositories hold all SQL and never import Flask. flask-smorest provides validation + OpenAPI from marshmallow schemas.

**Tech Stack:** Python 3.11, Flask 3, flask-smorest, marshmallow, PyMySQL, DBUtils pooling, gunicorn, pytest, Docker Compose (MySQL 8), GitHub Actions.

## Global Constraints

- Python 3.11. MySQL 8.
- No ORM. No SQLAlchemy, no Alembic. All SQL hand-written, all of it inside `app/repositories/`.
- No Flask import inside `app/services/` or `app/repositories/`.
- Money is `Decimal` end to end, never `float`.
- No secrets in the repo. Config from environment; production fails fast if unset.
- Every phase leaves the app runnable and the test suite green before commit.
- Conventional Commits. Work stays on branch `rework/corebank-api`; `main` untouched.

---

## Phase 0 — Runnable baseline + safety net

**Deliverable:** `docker compose up` runs the *current* app against containerized MySQL; characterization tests capture current behavior; CI skeleton runs them.

- [ ] `docker-compose.yml`: MySQL 8 with healthcheck + `api` service; env-driven config
- [ ] `Dockerfile` (multi-stage, non-root, gunicorn) — temporarily runs current `app.py`
- [ ] `.env.example`, `.gitignore` additions, `requirements.txt` split into prod + `requirements-dev.txt`
- [ ] `tests/conftest.py`: spin up schema + seed, provide Flask test client + admin/user tokens
- [ ] `tests/characterization/`: hit representative endpoints per resource, record status + shape; tag known-wrong behaviors `@pytest.mark.known_bug`
- [ ] `.github/workflows/ci.yml`: lint + MySQL service + pytest
- [ ] **Verify:** `docker compose up` serves Swagger; `pytest` green locally
- [ ] **Commit:** `chore: containerize baseline and add characterization tests`

## Phase 1 — Foundation (factory, config, pool, uow, migrations)

**Deliverable:** New `app/` package boots via `create_app()`; DB access flows through a pool and a unit of work; schema comes from migration files.

- [ ] `app/config.py` — `Base/Dev/Test/Prod` config classes; Prod raises if `JWT_SECRET_KEY`/DB creds unset
- [ ] `app/db/pool.py` — `PooledDB` over PyMySQL, `DictCursor`, `autocommit=False`
- [ ] `app/db/uow.py` — `unit_of_work()` context manager: BEGIN → yield conn → COMMIT / ROLLBACK-on-exception → return to pool
- [ ] `migrations/001_initial_schema.sql` (11 tables, verbatim), `002_indexes.sql` (FKs + reporting columns), `003_constraints.sql` (fix NOT NULL + ON DELETE SET NULL on `loan.customer_id`, `loan_payment.loan_id`)
- [ ] `scripts/migrate.py` — apply pending migrations, track in `schema_migrations`
- [ ] `seeds/demo_data.sql` — coherent demo dataset across all tables
- [ ] `app/__init__.py` — `create_app(config)`: smorest `Api`, JWT, CORS allowlist, blueprints, error handlers, `/health` + `/health/ready`
- [ ] `app/api/errors.py` — one JSON error envelope; register handlers
- [ ] **Verify:** `create_app` boots; `pytest tests/unit/test_uow.py` proves commit-on-success and rollback-on-raise against real MySQL
- [ ] **Commit:** `feat: add app factory, connection pool, unit of work, and migrations`

## Phase 2 — Repositories (all SQL, isolated)

**Deliverable:** Every query from the old routes lives in a repository function taking a connection; no Flask, no commits.

- [ ] One module per resource in `app/repositories/`: `customers, users, accounts, cards, branches, employees, loans, loan_payments, transactions, credit_scores, support_tickets`
- [ ] Port each SQL statement verbatim in intent; parameterized; return dicts/lists
- [ ] Money columns read/written as `Decimal`
- [ ] Preserve the three analytical queries as named functions: `branches_with_conditions`, `customers_with_high_transactions`, `top_resolvers`
- [ ] `tests/integration/test_repositories.py` — round-trip CRUD per repo against real MySQL
- [ ] `tests/architecture/test_layering.py` — no `cursor.execute`/SQL outside `app/repositories/`; no `flask` import in services/repositories
- [ ] **Verify:** integration + architecture tests green
- [ ] **Commit:** `feat: extract all SQL into repository layer`

## Phase 3 — Services + correctness fixes

**Deliverable:** Business logic in services owning transaction boundaries; the money-transfer defect class eliminated.

- [ ] `app/services/` one module per resource; services compose repositories inside `unit_of_work()`
- [ ] `transfer_service.transfer()`: single uow; lock both accounts `FOR UPDATE` ordered by id; reject self-transfer; debit via `UPDATE … WHERE balance >= %s` asserting rowcount; credit; record; all-or-nothing
- [ ] `Decimal` money everywhere; quantize to 2 places
- [ ] Delete the fake anti-SQLi regex in login; rely on parameterization + schema
- [ ] Ownership rules: a USER may act only on their own customer/accounts/cards/loans/transactions; ADMIN unrestricted
- [ ] `tests/unit/` — services against **fake repositories**: overdraft rejected, self-transfer rejected, transfer conserves balance, ownership enforced
- [ ] **Verify:** unit tests green with no DB
- [ ] **Commit:** `feat: add service layer with atomic transfers and correctness fixes`

## Phase 4 — API layer (flask-smorest, /api/v1)

**Deliverable:** All 62 endpoints served as thin smorest views under `/api/v1`; validation + OpenAPI from schemas; auth + ownership enforced.

- [ ] `app/api/schemas/` — marshmallow schemas per resource (request + response)
- [ ] `app/security/` — `jwt_required`, `admin_required`, ownership helpers
- [ ] One `MethodView`-based module per resource in `app/api/`; call services only
- [ ] Register all blueprints under `/api/v1`; Swagger UI at `/docs`
- [ ] `tests/integration/test_api_flows.py` — auth → create → read → transfer → report happy paths + auth/ownership failures
- [ ] Update/convert characterization tests to the new contract; flip `known_bug` markers
- [ ] **Verify:** full request→response suite green; Swagger UI lists every endpoint
- [ ] **Commit:** `feat: rebuild HTTP layer on flask-smorest with validation and versioned routes`

## Phase 5 — Concurrency proof + coverage

**Deliverable:** The centerpiece test; coverage at target.

- [ ] `tests/concurrency/test_balance_conservation.py` — N threads, M accounts, random transfers; assert total balance invariant and no negative balance
- [ ] Capture it failing against the pre-fix transfer (documented), passing against the fixed one
- [ ] Fill unit/integration gaps to ~80% on services + repositories
- [ ] **Verify:** `pytest --cov=app` meets target; concurrency test green
- [ ] **Commit:** `test: add concurrency balance-conservation proof and raise coverage`

## Phase 6 — Ops polish

**Deliverable:** Production-shaped container + green CI.

- [ ] Dockerfile → gunicorn serving `create_app()`; entrypoint runs migrations then seeds (dev)
- [ ] Structured JSON logging with per-request id
- [ ] CI matrix: ruff, black --check, pytest+cov against MySQL service; coverage artifact
- [ ] **Verify:** `docker compose up` clean-clone works; CI green on push
- [ ] **Commit:** `chore: production Dockerfile, structured logging, and CI`

## Phase 7 — Presentation + rename

**Deliverable:** A repo that sells itself.

- [ ] `README.md` per spec §7 (badges, quickstart, Mermaid architecture + ER diagrams, 3 analytical queries with their business questions, transfer before/after, API reference, testing, structure, roadmap, breaking-changes note)
- [ ] `LICENSE` (MIT, current year, owner name)
- [ ] Move spec to `docs/design.md`; remove `diagramPhoto.jpeg`
- [ ] Delete dead `app.py`/`database.py`/`routes/` once parity confirmed
- [ ] Prepare repo metadata (description, topics) and rename instructions for owner
- [ ] **Verify:** README renders with both diagrams; fresh clone → `docker compose up` → working seeded API
- [ ] **Commit:** `docs: add README, license, and diagrams; retire legacy layout`

## Self-review notes

- Spec coverage: every §2–§7 item maps to a phase above. §3 fixes 1–6 → Phase 3; 7,10,11,12 → Phases 1/0; 8 → Phases 3–4; 9 → Phase 1 pool.
- The pre-fix concurrency capture (Phase 5) depends on keeping the legacy transfer reachable until Phase 5; legacy files are deleted only in Phase 7.
- Risk: flask-smorest port is the largest phase; if time-boxed, resources convert independently so partial completion still leaves a coherent subset running.
