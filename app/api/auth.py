"""Authentication endpoints."""

from __future__ import annotations

from flask.views import MethodView
from flask_jwt_extended import create_access_token, jwt_required
from flask_smorest import Blueprint
from marshmallow import Schema, fields

from app.security import current_user
from app.services import auth_service

blp = Blueprint("auth", __name__, description="Authentication and tokens")


class LoginSchema(Schema):
    username = fields.String(required=True, metadata={"example": "alice"})
    password = fields.String(required=True, load_only=True, metadata={"example": "alice123"})


class TokenSchema(Schema):
    access_token = fields.String()
    token_type = fields.String()


class IdentitySchema(Schema):
    user_id = fields.String()
    role = fields.String()
    customer_id = fields.String(allow_none=True)


@blp.route("/login")
class Login(MethodView):
    @blp.arguments(LoginSchema)
    @blp.response(200, TokenSchema)
    def post(self, data):
        """Exchange username and password for a JWT access token."""
        who = auth_service.authenticate(data["username"], data["password"])
        token = create_access_token(
            identity=who["user_id"],
            additional_claims={"role": who["role"], "customer_id": who["customer_id"]},
        )
        return {"access_token": token, "token_type": "bearer"}


@blp.route("/me")
class Me(MethodView):
    @jwt_required()
    @blp.response(200, IdentitySchema)
    def get(self):
        """Return the identity encoded in the current token."""
        return current_user()
