"""Structured JSON logging with a per-request id.

Each log line is a single JSON object, which reads cleanly in container logs and
ships straight into log aggregators without a custom parser.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from flask import Flask, g, has_request_context, request


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if has_request_context():
            payload["request_id"] = getattr(g, "request_id", None)
            payload["method"] = request.method
            payload["path"] = request.path
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(app: Flask) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if app.config.get("DEBUG") else logging.INFO)

    app.logger.handlers.clear()
    app.logger.propagate = True

    @app.before_request
    def _assign_request_id() -> None:
        g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    @app.after_request
    def _log_request(response):
        app.logger.info("request completed status=%s", response.status_code)
        response.headers["X-Request-ID"] = getattr(g, "request_id", "")
        return response
