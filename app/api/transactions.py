"""Transaction and money-transfer endpoints."""
from __future__ import annotations

from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint
from flask.views import MethodView
from marshmallow import Schema, fields, validate

from app.security import admin_required, current_user
from app.services import transaction_service

from ._fields import money

blp = Blueprint("transactions", __name__, description="Ledger and transfers")

TXN_TYPES = ("DEPOSIT", "WITHDRAWAL", "TRANSFER")


class TransactionSchema(Schema):
    transaction_id = fields.String(dump_only=True)
    from_account_id = fields.String(required=True)
    to_account_id = fields.String(allow_none=True)
    transaction_type = fields.String(validate=validate.OneOf(TXN_TYPES))
    amount = money(required=True)
    transaction_timestamp = fields.DateTime(dump_only=True)


class TransferSchema(Schema):
    sender_account_id = fields.String(required=True)
    receiver_account_id = fields.String(required=True)
    amount = money(required=True, validate=validate.Range(min=0, min_inclusive=False))


class HighValueSchema(Schema):
    customer_id = fields.String()
    first_name = fields.String()
    last_name = fields.String()
    total_transaction = money()


@blp.route("/")
class Transactions(MethodView):
    @admin_required
    @blp.response(200, TransactionSchema(many=True))
    def get(self):
        """List all transactions (admin)."""
        return transaction_service.list_all()


@blp.route("/<transaction_id>")
class Transaction(MethodView):
    @jwt_required()
    @blp.response(200, TransactionSchema)
    def get(self, transaction_id):
        """Fetch one transaction (party to it, or admin)."""
        return transaction_service.get(transaction_id, current_user())

    @admin_required
    @blp.response(204)
    def delete(self, transaction_id):
        """Delete a transaction record (admin)."""
        transaction_service.delete(transaction_id)
        return ""


@blp.route("/by-account/<account_id>")
class AccountTransactions(MethodView):
    @jwt_required()
    @blp.response(200, TransactionSchema(many=True))
    def get(self, account_id):
        """List transactions for an account (owner or admin)."""
        return transaction_service.list_by_account(account_id, current_user())


@blp.route("/transfer")
class Transfer(MethodView):
    @jwt_required()
    @blp.arguments(TransferSchema)
    @blp.response(201, TransactionSchema)
    def post(self, data):
        """Transfer money between two accounts, atomically."""
        return transaction_service.transfer(
            current_user(),
            data["sender_account_id"],
            data["receiver_account_id"],
            data["amount"],
        )


@blp.route("/reports/high-value/<minimum>")
class HighValue(MethodView):
    @admin_required
    @blp.response(200, HighValueSchema(many=True))
    def get(self, minimum):
        """Customers whose transactions sum above a threshold (admin)."""
        return transaction_service.high_transactions(minimum)
