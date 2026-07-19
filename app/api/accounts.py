"""Account endpoints."""
from __future__ import annotations

from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint
from flask.views import MethodView
from marshmallow import Schema, fields, validate

from app.security import admin_required, current_user
from app.services import account_service

from ._fields import money

blp = Blueprint("accounts", __name__, description="Bank accounts")

ACCOUNT_TYPES = ("CHECKING", "SAVINGS")


class AccountSchema(Schema):
    account_id = fields.String(dump_only=True)
    customer_id = fields.String(required=True)
    account_type = fields.String(validate=validate.OneOf(ACCOUNT_TYPES))
    balance = money(dump_only=True)
    creation_date = fields.DateTime(dump_only=True)
    branch_id = fields.String(required=True)


class AccountCreateSchema(Schema):
    customer_id = fields.String(required=True)
    account_type = fields.String(required=True, validate=validate.OneOf(ACCOUNT_TYPES))
    branch_id = fields.String(required=True)


class BalanceUpdateSchema(Schema):
    balance = money(required=True)


@blp.route("/")
class Accounts(MethodView):
    @jwt_required()
    @blp.response(200, AccountSchema(many=True))
    def get(self):
        """List accounts (customers see only their own)."""
        return account_service.list_for_actor(current_user())

    @admin_required
    @blp.arguments(AccountCreateSchema)
    @blp.response(201, AccountSchema)
    def post(self, data):
        """Open a new account (admin)."""
        return account_service.create(
            data["customer_id"], data["account_type"], data["branch_id"]
        )


@blp.route("/<account_id>")
class Account(MethodView):
    @jwt_required()
    @blp.response(200, AccountSchema)
    def get(self, account_id):
        """Fetch one account (owner or admin)."""
        return account_service.get(account_id, current_user())

    @admin_required
    @blp.response(204)
    def delete(self, account_id):
        """Close an account (admin)."""
        account_service.delete(account_id)
        return ""


@blp.route("/<account_id>/balance")
class AccountBalance(MethodView):
    @admin_required
    @blp.arguments(BalanceUpdateSchema)
    @blp.response(200, AccountSchema)
    def put(self, data, account_id):
        """Set an account balance directly (admin)."""
        return account_service.set_balance(account_id, data["balance"])
