"""A single JSON error envelope for the whole API.

    { "code": 404, "status": "Not Found", "message": "...", "errors": {...} }

The ``errors`` key is present only for field-level validation failures, matching
the shape flask-smorest emits for schema validation so clients see one format.
"""
from __future__ import annotations

from http import HTTPStatus

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from app.services.exceptions import AppError


def _envelope(code: int, message: str, errors: dict | None = None):
    try:
        status = HTTPStatus(code).phrase
    except ValueError:
        status = "Error"
    body = {"code": code, "status": status, "message": message}
    if errors:
        body["errors"] = errors
    return jsonify(body), code


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def _handle_app_error(exc: AppError):
        return _envelope(exc.status_code, exc.message, exc.errors)

    @app.errorhandler(HTTPException)
    def _handle_http_error(exc: HTTPException):
        # flask-smorest/webargs attach validation detail under data["messages"];
        # some paths use data["errors"]. Surface either as the envelope's errors.
        data = getattr(exc, "data", None) or {}
        errors = data.get("errors") or data.get("messages")
        message = "Validation failed" if errors else (exc.description or exc.name)
        return _envelope(exc.code or 500, message, errors)

    @app.errorhandler(Exception)
    def _handle_unexpected(exc: Exception):
        app.logger.exception("Unhandled exception")
        return _envelope(500, "Internal server error")
