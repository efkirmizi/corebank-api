"""Authorization helpers layered on flask-jwt-extended.

The access token carries the user's role and, for customer users, their
``customer_id``. Ownership checks therefore compare the token's customer_id to a
resource's customer_id with no extra database round-trip.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps

from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from app.services.exceptions import ForbiddenError

ADMIN = "ADMIN"


def current_user() -> dict:
    """Return the authenticated principal. Requires a verified request."""
    claims = get_jwt()
    return {
        "user_id": get_jwt_identity(),
        "role": claims.get("role"),
        "customer_id": claims.get("customer_id"),
    }


def is_admin() -> bool:
    return get_jwt().get("role") == ADMIN


def admin_required(fn: Callable) -> Callable:
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        if get_jwt().get("role") != ADMIN:
            raise ForbiddenError("Administrator access required")
        return fn(*args, **kwargs)

    return wrapper


def require_owner_or_admin(customer_id: str | None) -> None:
    """Allow admins through; otherwise the caller must own the resource."""
    claims = get_jwt()
    if claims.get("role") == ADMIN:
        return
    if not customer_id or claims.get("customer_id") != customer_id:
        raise ForbiddenError("You do not have access to this resource")


def register_jwt_handlers(jwt) -> None:
    """Make JWT auth failures use the same error envelope as everything else."""

    def _envelope(code: int, status: str, message: str):
        return {"code": code, "status": status, "message": message}, code

    @jwt.unauthorized_loader
    def _missing(reason):  # noqa: ANN001
        return _envelope(401, "Unauthorized", "Missing or malformed Authorization header")

    @jwt.invalid_token_loader
    def _invalid(reason):  # noqa: ANN001
        return _envelope(401, "Unauthorized", "Invalid authentication token")

    @jwt.expired_token_loader
    def _expired(header, payload):  # noqa: ANN001
        return _envelope(401, "Unauthorized", "Authentication token has expired")

    @jwt.revoked_token_loader
    def _revoked(header, payload):  # noqa: ANN001
        return _envelope(401, "Unauthorized", "Authentication token has been revoked")
