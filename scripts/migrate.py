"""Apply pending SQL migrations in order.

Usage:
    python -m scripts.migrate            # apply everything pending
    python -m scripts.migrate --seed     # then load seeds/demo_data.sql

Applied versions are tracked in the ``schema_migrations`` table, so re-running
is safe and idempotent. This replaces the old ``init_db()``-at-import approach.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pymysql

ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = ROOT / "migrations"
SEEDS_FILE = ROOT / "seeds" / "demo_data.sql"


def _connect(database: str | None):
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=database,
        charset="utf8mb4",
        autocommit=True,
    )


def _statements(sql: str):
    """Yield individual statements, dropping full-line -- comments and blanks."""
    lines = [ln for ln in sql.splitlines() if not ln.strip().startswith("--")]
    for chunk in "\n".join(lines).split(";"):
        if chunk.strip():
            yield chunk.strip()


def ensure_database() -> str:
    name = os.getenv("DB_NAME", "bank")
    conn = _connect(None)
    with conn.cursor() as cur:
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{name}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
    conn.close()
    return name


def _ensure_migrations_table(cur) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(255) PRIMARY KEY,
            applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _applied(cur) -> set[str]:
    cur.execute("SELECT version FROM schema_migrations")
    return {row[0] for row in cur.fetchall()}


def run_migrations() -> int:
    name = ensure_database()
    conn = _connect(name)
    applied_count = 0
    try:
        with conn.cursor() as cur:
            _ensure_migrations_table(cur)
            done = _applied(cur)
            for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
                version = path.stem
                if version in done:
                    continue
                print(f"applying {version} ...")
                for stmt in _statements(path.read_text(encoding="utf-8")):
                    cur.execute(stmt)
                cur.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s)", (version,)
                )
                applied_count += 1
    finally:
        conn.close()
    print(f"done: {applied_count} migration(s) applied.")
    return applied_count


def load_seeds() -> None:
    if not SEEDS_FILE.exists():
        print("no seed file, skipping.")
        return
    name = os.getenv("DB_NAME", "bank")
    conn = _connect(name)
    try:
        with conn.cursor() as cur:
            for stmt in _statements(SEEDS_FILE.read_text(encoding="utf-8")):
                cur.execute(stmt)
        print("seeds loaded.")
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply database migrations.")
    parser.add_argument("--seed", action="store_true", help="load demo seed data after migrating")
    args = parser.parse_args()
    run_migrations()
    if args.seed:
        load_seeds()
    return 0


if __name__ == "__main__":
    sys.exit(main())
