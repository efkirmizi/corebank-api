"""Domain exceptions raised by the service layer.

Deliberately free of any Flask import: services stay testable without an app
context, and the API layer is the only place that maps these to HTTP responses.
"""

from __future__ import annotations


class AppError(Exception):
    status_code = 500
    default_message = "Internal server error"

    def __init__(self, message: str | None = None, *, errors: dict | None = None):
        super().__init__(message or self.default_message)
        self.message = message or self.default_message
        self.errors = errors


class BadRequestError(AppError):
    status_code = 400
    default_message = "Bad request"


class AuthError(AppError):
    status_code = 401
    default_message = "Authentication failed"


class ForbiddenError(AppError):
    status_code = 403
    default_message = "Access forbidden"


class NotFoundError(AppError):
    status_code = 404
    default_message = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    default_message = "Conflict"


class BusinessRuleError(AppError):
    """A request that is well-formed but violates a banking rule
    (e.g. insufficient funds, self-transfer)."""

    status_code = 422
    default_message = "Business rule violation"
