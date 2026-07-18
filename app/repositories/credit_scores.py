"""SQL for the credit_score table."""
from __future__ import annotations

from pymysql.connections import Connection

from ._base import execute, fetch_all, fetch_one

COLUMNS = "credit_score_id, customer_id, score, risk_category, computed_by_system"


def insert(conn: Connection, data: dict) -> None:
    execute(
        conn,
        "INSERT INTO credit_score (credit_score_id, customer_id, score, "
        "risk_category, computed_by_system) VALUES (%(credit_score_id)s, "
        "%(customer_id)s, %(score)s, %(risk_category)s, %(computed_by_system)s)",
        data,
    )


def list_all(conn: Connection) -> list[dict]:
    return fetch_all(conn, f"SELECT {COLUMNS} FROM credit_score")


def get(conn: Connection, credit_score_id: str) -> dict | None:
    return fetch_one(
        conn,
        f"SELECT {COLUMNS} FROM credit_score WHERE credit_score_id = %s",
        (credit_score_id,),
    )


def update(conn: Connection, credit_score_id: str, fields: dict) -> int:
    assignments = ", ".join(f"{col} = %({col})s" for col in fields)
    params = {**fields, "credit_score_id": credit_score_id}
    return execute(
        conn,
        f"UPDATE credit_score SET {assignments} WHERE credit_score_id = %(credit_score_id)s",
        params,
    )


def delete(conn: Connection, credit_score_id: str) -> int:
    return execute(
        conn, "DELETE FROM credit_score WHERE credit_score_id = %s", (credit_score_id,)
    )
