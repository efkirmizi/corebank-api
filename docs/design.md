# corebank-api — Design

**Date:** 2026-07-19
**Status:** Approved
**Repository:** `efkirmizi/Banking-API` → to be renamed `efkirmizi/corebank-api`

## 1. Context

The repository holds a Flask + MySQL banking REST API built as a university database
course project: ~4,300 lines across 13 route modules, 62 endpoints, 11 tables, JWT
auth with ADMIN/USER roles, and Swagger docs generated from docstrings. All SQL is
hand-written.

It currently has no README, no LICENSE, no tests, and no CI. Secrets are hardcoded.
`init_db()` executes at import time, so the app cannot start without a preconfigured
local MySQL instance — a reviewer cannot run it.

### Goal

Turn it into a portfolio piece that survives both a 30-second skim by a recruiter and
a close read by a hiring engineer. The repo must demonstrate four things, all of which
the owner named as required:

1. **SQL depth** — hand-written SQL is preserved and showcased, never replaced by an ORM.
2. **Architecture** — clear layering with enforced boundaries.
3. **Correctness and safety** — a banking API that handles money correctly under concurrency.
4. **Production readiness** — runs in one command, tested in CI.

### Non-goals

- No ORM. No SQLAlchemy, no Alembic. The raw SQL is the point.
- No hosted live demo. A DB-backed demo costs money and rots; a dead link is worse than none.
- No frontend.
- No new banking features. This is a hardening and restructuring effort, not feature work.
- No rewrite of existing git history.
- No idempotency keys on transfers (considered and explicitly deferred to the roadmap).

## 2. Target architecture

```
corebank-api/
├── app/
│   ├── __init__.py            create_app() factory
│   ├── config.py              Dev/Test/Prod config from environment
│   ├── extensions.py          jwt, cors, api singletons
│   ├── api/                   thin HTTP layer
│   │   ├── __init__.py        blueprint registration under /api/v1
│   │   ├── accounts.py
│   │   ├── transactions.py
│   │   ├── … one module per resource
│   │   ├── schemas/           marshmallow request/response schemas
│   │   └── errors.py          centralized error handlers
│   ├── services/              business logic, owns transaction boundaries
│   ├── repositories/          every hand-written SQL query, nothing else
│   ├── db/
│   │   ├── pool.py            DBUtils PooledDB over PyMySQL
│   │   └── uow.py             unit-of-work context manager
│   └── security/              jwt_required, admin_required, ownership checks
├── migrations/                001_initial_schema.sql, 002_indexes.sql, …
├── seeds/                     demo_data.sql
├── scripts/migrate.py         migration runner
├── tests/
│   ├── unit/                  services against fake repositories
│   ├── integration/           repositories + API flows against real MySQL
│   ├── concurrency/           balance-conservation test
│   └── architecture/          dependency-rule enforcement
├── docs/
├── .github/workflows/ci.yml
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── README.md
└── LICENSE
```

### The dependency rule

Dependencies point inward only:

```
api  →  services  →  repositories  →  db
```

Two invariants, both mechanically checkable:

- **No SQL outside `app/repositories/`.** No `cursor.execute` or SQL keyword strings
  anywhere else.
- **No Flask import inside `app/repositories/` or `app/services/`.** This is what makes
  services unit-testable with no app context and no database.

`tests/architecture/test_layering.py` asserts both by scanning the source tree, so a
violation fails CI rather than relying on discipline.

### Unit of work

Repositories accept a connection instead of opening their own. That is what allows
several repository calls to share one atomic transaction:

```python
with unit_of_work() as uow:                      # BEGIN
    accounts.debit(uow, sender_id, amount)       # SELECT … FOR UPDATE
    accounts.credit(uow, receiver_id, amount)
    transactions.record(uow, transfer)
                                                 # COMMIT on exit, ROLLBACK on exception
```

Services own the transaction boundary. Repositories never commit. This makes the
existing money-transfer bug structurally impossible to reintroduce rather than merely
fixed once.

Lock ordering: when a transfer locks two accounts, it locks them sorted by `account_id`
so concurrent opposing transfers cannot deadlock.

### HTTP layer

`flasgger` is replaced by **flask-smorest** (marshmallow + apispec). This collapses three
concerns into one declaration — validation, serialization, and OpenAPI generation:

```python
@blp.route("/accounts")
class Accounts(MethodView):
    @blp.arguments(AccountCreateSchema)
    @blp.response(201, AccountSchema)
    def post(self, data): ...
```

Rationale: Swagger docstrings are currently ~85% of every route file (`create_account`
is 40 lines of YAML around 45 lines of Python). Generating the spec from the same schema
that validates the request means documentation cannot drift from behavior, and route
files shrink roughly fivefold.

All routes move under `/api/v1`. Errors use one documented JSON envelope:

```json
{ "code": 400, "status": "Bad Request", "message": "…", "errors": { "field": ["…"] } }
```

## 3. Correctness fixes

| # | Issue | Location | Fix |
|---|---|---|---|
| 1 | Transfer is two bare UPDATEs with no transaction, locking, or rollback — a failure between them destroys money | `routes/transaction.py:565` | Unit of work, `SELECT … FOR UPDATE` ordered by account id, rollback on any exception |
| 2 | `float()` arithmetic on currency | `routes/transaction.py:562` | `Decimal` end to end; never convert money to float |
| 3 | Overdraft checked in Python, so it fails under concurrency | `routes/transaction.py:562` | Enforce in SQL: `UPDATE … WHERE balance >= %s`, assert `rowcount == 1`; DB CHECK constraint as backstop |
| 4 | Self-transfer permitted — records a transaction that nets zero | `routes/transaction.py:544` | Reject `sender_account_id == receiver_account_id` with 400 |
| 5 | Error body returned with HTTP 200 | `routes/transaction.py:334` | Centralized error handlers; audit all 62 endpoints |
| 6 | Regex strips characters from username "to prevent SQL injection" on an already-parameterized query — and makes users `a-b` and `ab` collide at login | `routes/auth.py:66` | Delete it; validate with a schema instead |
| 7 | Hardcoded JWT secret and DB password | `app.py:12`, `database.py:7` | Environment config; fail fast at startup if unset in production |
| 8 | Ownership gaps — endpoints check role but not resource ownership | across `routes/` | Audit every endpoint; a USER may only read their own customer, accounts, cards, loans, and transactions |
| 9 | Connections leak on error paths that return before `close()` | across `routes/` | Pool plus context manager; no manual close calls remain |
| 10 | `uuid==1.30` shadows the stdlib module; three MySQL drivers pinned | `requirements.txt` | PyMySQL only; split `requirements.txt` / `requirements-dev.txt` |
| 11 | `init_db()` runs at import, crashing the app without a DB | `app.py:39` | Versioned migrations run explicitly via `scripts/migrate.py` |
| 12 | CORS open to all origins | `app.py:10` | Configurable allowlist, permissive only in development |

## 4. Data layer

**Migrations.** Numbered `.sql` files applied in order by `scripts/migrate.py`, with
applied versions tracked in a `schema_migrations` table. Versioned and repeatable while
staying hand-written SQL — no ORM, no Alembic.

- `001_initial_schema.sql` — the 11 tables.
- `002_indexes.sql` — indexes on foreign keys and on columns the analytical queries
  filter and group by. Originally only primary and unique keys existed, so the three
  reporting queries did full scans.

**Revised during implementation.** The plan called for a third migration to correct the
two foreign keys declared `ON DELETE SET NULL` on `NOT NULL` columns
(`loan.customer_id`, `loan_payment.loan_id`). That proved impossible to stage as a later
migration: MySQL 8 rejects the combination at table-creation time (error 1830), so a
faithful reproduction of the original schema cannot be created at all — the original
`init_db()` could never have run on MySQL 8. The correction is therefore folded into
`001` (both use `ON DELETE RESTRICT`, which is what a `NOT NULL` owning column implies)
and documented there and in the README.

**Pooling.** `DBUtils.PooledDB` over PyMySQL, configured per environment, exposed only
through `app/db/`.

**Seeds.** `seeds/demo_data.sql` — branches, employees, customers, accounts with
balances, cards, loans, transactions, and support tickets. Enough for every endpoint to
return meaningful data and for the analytical queries to produce interesting rows.
Loaded automatically by Docker Compose so a reviewer sees a populated API immediately.

## 5. Testing

**Characterization first.** Before restructuring, stand up MySQL in Docker, exercise all
62 endpoints against the current code, and record status codes and response shapes as a
regression baseline. Where a characterization test captures behavior known to be wrong
(items 4, 5, and 6 above), it is tagged `@pytest.mark.known_bug` and flipped in the same
commit as its fix, so the diff shows intent rather than silently changing a contract.

| Layer | Scope | Speed |
|---|---|---|
| Unit | Services against fake repositories: overdraft, self-transfer, loan amortization, credit-score banding | Milliseconds, no DB |
| Integration | Repositories against real MySQL 8 so SQL typos and schema drift fail; full request→response flows via Flask test client | Seconds |
| Concurrency | N threads transferring randomly among M accounts; assert total system balance is invariant and no balance goes negative | Seconds |
| Architecture | Dependency rule: no SQL outside repositories, no Flask inside services or repositories | Milliseconds |

The concurrency test is run against the pre-fix code to capture the failure and against
the fixed code to show it passing. That before/after is reproduced in the README; it is
the most convincing single artifact in the repository.

Coverage target ~80% on `app/services/` and `app/repositories/`. Not chasing 100%.

## 6. Operations

- **`docker compose up`** brings up API + MySQL 8 with healthchecks, runs migrations,
  loads seeds, and serves Swagger UI. One command, no local MySQL install. This is the
  promise the README opens with, and it must work from a clean clone.
- **Dockerfile** — multi-stage, non-root user, gunicorn. No `flask run --debug`.
- **CI** — GitHub Actions on push and pull request: ruff, black `--check`, MySQL service
  container, full pytest suite, coverage report. Status badge in the README.
- **Config** — `.env.example` committed, `.env` gitignored, `config.py` with
  Dev/Test/Prod classes. Production config raises at startup if `JWT_SECRET_KEY` or DB
  credentials are unset.
- **Ops surface** — `/health` (liveness) and `/health/ready` (DB reachable), structured
  JSON logging with a request ID per request.

## 7. Presentation

README section order, matching how a skimmer actually reads:

1. Title, one-line description, badges (CI, license, Python version)
2. What it is, in two sentences, with honest framing: built as a course project, hardened into a production-shaped service
3. Quickstart — `docker compose up`, then a Swagger UI link. Copy-pasteable.
4. Architecture diagram (Mermaid)
5. ER diagram (Mermaid `erDiagram`, replacing `diagramPhoto.jpeg` — diffable, no image hosting)
6. The three analytical queries shown inline, each with the business question it answers
7. Transaction safety — the concurrency test, before and after
8. API reference, 62 endpoints grouped by resource
9. Testing — how to run, what each layer covers
10. Project structure
11. Roadmap — including idempotency keys, explicitly deferred
12. License (MIT)

Mermaid renders natively on GitHub, so there are no image assets to host or rot.

**Repository metadata.** Description: "Core banking REST API — Flask, MySQL, JWT,
hand-written SQL, fully containerized." Topics: `flask`, `mysql`, `rest-api`, `jwt`,
`banking`, `python`, `docker`, `openapi`, `pytest`.

**Rename** to `corebank-api`. "Core banking" is the correct industry term for the
modeled domain — accounts, cards, loans, branches, ledger — so the name signals domain
literacy while staying instantly legible in a repo list. GitHub redirects the old URL,
so nothing breaks. The rename requires the owner (no `gh` CLI is installed on this
machine) and is performed at the end, after the content justifies the name.

**Git history** is left intact. Existing commits (`hmm`, `something something`) stay;
new commits are clean and conventional. Rewriting published history is disruptive, and
the contrast makes the new work read better.

This spec is published at `docs/design.md`, alongside the phased
`docs/implementation-plan.md`, so the repository carries its own design record.

## 8. Execution order

Each phase leaves the test suite green.

| Phase | Work |
|---|---|
| 0 | Docker Compose + MySQL, current app running, characterization tests, CI skeleton |
| 1 | App factory, config, connection pool, unit of work, migrations, error envelope |
| 2 | Extract all SQL into repositories |
| 3 | Services with transaction boundaries; correctness fixes 1–6 |
| 4 | flask-smorest API layer, schemas, `/api/v1`, auth and ownership fixes (8) |
| 5 | Unit, integration, concurrency, and architecture tests to target coverage |
| 6 | Dockerfile, compose polish, CI, health checks, structured logging |
| 7 | README, Mermaid diagrams, LICENSE, repo metadata, rename |

## 9. Risks

| Risk | Mitigation |
|---|---|
| Behavior drift across 4,300 restructured lines | Characterization tests written and green before any refactoring begins |
| flask-smorest migration touches all 62 endpoints | Phase 4 is a single focused phase; characterization tests catch contract changes; resource modules convert one at a time |
| Ownership audit (fix 8) changes who can access what, breaking existing clients | It is a security fix and intentionally breaking; documented in the README under a "Breaking changes" heading |
| Scope is large for one pass | Phases are independently shippable; work can stop after any phase with the repo in a better and consistent state |
| Concurrency test is flaky under CI load | Assert invariants (balance conservation, non-negativity) rather than timings; fixed seed; retry budget of zero — a flake means a real bug |

## 10. Success criteria

- `git clone && docker compose up` yields a working, seeded API with Swagger UI, on a machine with no MySQL installed.
- Full test suite green in GitHub Actions, badge passing.
- Concurrency test demonstrates balance conservation, and fails against the pre-fix implementation.
- Architecture test passes: no SQL outside repositories, no Flask inside services or repositories.
- No secrets in the repository; `.env.example` documents every required variable.
- README renders with both Mermaid diagrams on GitHub.
- Repository renamed to `corebank-api` with description and topics set.
