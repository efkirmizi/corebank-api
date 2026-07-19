"""Liveness and readiness probes."""
from __future__ import annotations

from flask import jsonify
from flask_smorest import Blueprint

from app.db import ping

blp = Blueprint("health", __name__, description="Service health checks")


@blp.route("/health", methods=["GET"])
def health():
    """Liveness — the process is up and serving."""
    return jsonify({"status": "ok"})


@blp.route("/health/ready", methods=["GET"])
def ready():
    """Readiness — the database is reachable."""
    try:
        ping()
    except Exception:
        return jsonify({"status": "unavailable", "database": "unreachable"}), 503
    return jsonify({"status": "ready", "database": "reachable"})
