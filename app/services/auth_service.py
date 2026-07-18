"""Authentication: verify credentials, return the principal for token minting.

The service validates the password and hands back identity + claims. Creating
the JWT itself is the API layer's job, keeping this layer Flask-free. Note the
deliberate absence of the old username-sanitizing regex: the query is
parameterized, so stripping characters added no safety and silently merged
distinct usernames (``a-b`` and ``ab``) at login.
"""
from __future__ import annotations

from werkzeug.security import check_password_hash

from app.db import read_only
from app.repositories import users

from .exceptions import AuthError


def authenticate(username: str, password: str) -> dict:
    with read_only() as conn:
        user = users.get_by_username(conn, username)

    if not user or not check_password_hash(user["password"], password):
        # Same error whether the user is unknown or the password is wrong,
        # so the response does not reveal which usernames exist.
        raise AuthError("Invalid credentials")

    return {
        "user_id": user["user_id"],
        "role": user["role"],
        "customer_id": user["customer_id"],
    }
