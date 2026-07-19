"""User (login identity) endpoints. Admin-managed."""

from __future__ import annotations

from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, fields, validate

from app.security import admin_required
from app.services import user_service

blp = Blueprint("users", __name__, description="Login identities (admin)")

ROLES = ("ADMIN", "USER")


class UserSchema(Schema):
    user_id = fields.String(dump_only=True)
    username = fields.String(required=True)
    role = fields.String(validate=validate.OneOf(ROLES))
    customer_id = fields.String(allow_none=True)


class UserCreateSchema(Schema):
    username = fields.String(required=True, validate=validate.Length(min=3, max=100))
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=6))
    role = fields.String(load_default="USER", validate=validate.OneOf(ROLES))
    customer_id = fields.String(allow_none=True, load_default=None)


class UserUpdateSchema(Schema):
    username = fields.String(validate=validate.Length(min=3, max=100))
    password = fields.String(load_only=True, validate=validate.Length(min=6))
    role = fields.String(validate=validate.OneOf(ROLES))
    customer_id = fields.String(allow_none=True)


@blp.route("/")
class Users(MethodView):
    @admin_required
    @blp.response(200, UserSchema(many=True))
    def get(self):
        """List users (admin)."""
        return user_service.list_all()

    @admin_required
    @blp.arguments(UserCreateSchema)
    @blp.response(201, UserSchema)
    def post(self, data):
        """Create a user (admin). Passwords are hashed before storage."""
        return user_service.create(
            data["username"], data["password"], data["role"], data.get("customer_id")
        )


@blp.route("/<user_id>")
class User(MethodView):
    @admin_required
    @blp.response(200, UserSchema)
    def get(self, user_id):
        """Fetch one user (admin)."""
        return user_service.get(user_id)

    @admin_required
    @blp.arguments(UserUpdateSchema)
    @blp.response(200, UserSchema)
    def put(self, data, user_id):
        """Update a user (admin)."""
        if not data:
            from app.services.exceptions import BadRequestError

            raise BadRequestError("No fields to update")
        return user_service.update(user_id, data)

    @admin_required
    @blp.response(204)
    def delete(self, user_id):
        """Delete a user (admin)."""
        user_service.delete(user_id)
        return ""
