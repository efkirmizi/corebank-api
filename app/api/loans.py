"""Loan endpoints."""
from __future__ import annotations

from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint
from flask.views import MethodView
from marshmallow import Schema, fields, validate

from app.security import admin_required, current_user
from app.services import loan_service

from ._fields import money

blp = Blueprint("loans", __name__, description="Loans")

LOAN_TYPES = ("HOME", "AUTO", "PERSONAL")
LOAN_STATUSES = ("ACTIVE", "PAID_OFF", "DEFAULT")


class LoanSchema(Schema):
    loan_id = fields.String(dump_only=True)
    customer_id = fields.String(required=True)
    loan_type = fields.String(required=True, validate=validate.OneOf(LOAN_TYPES))
    principal_amount = money(required=True, validate=validate.Range(min=0, min_inclusive=False))
    interest_rate = fields.Decimal(places=2, as_string=True, required=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    status = fields.String(load_default="ACTIVE", validate=validate.OneOf(LOAN_STATUSES))


class LoanStatusSchema(Schema):
    status = fields.String(required=True, validate=validate.OneOf(LOAN_STATUSES))


@blp.route("/")
class Loans(MethodView):
    @admin_required
    @blp.response(200, LoanSchema(many=True))
    def get(self):
        """List loans (admin)."""
        return loan_service.list_all()

    @admin_required
    @blp.arguments(LoanSchema)
    @blp.response(201, LoanSchema)
    def post(self, data):
        """Open a loan (admin)."""
        return loan_service.create(data)


@blp.route("/<loan_id>")
class Loan(MethodView):
    @jwt_required()
    @blp.response(200, LoanSchema)
    def get(self, loan_id):
        """Fetch one loan (owner or admin)."""
        return loan_service.get(loan_id, current_user())

    @admin_required
    @blp.response(204)
    def delete(self, loan_id):
        """Delete a loan (admin)."""
        loan_service.delete(loan_id)
        return ""


@blp.route("/<loan_id>/status")
class LoanStatus(MethodView):
    @admin_required
    @blp.arguments(LoanStatusSchema)
    @blp.response(200, LoanSchema)
    def put(self, data, loan_id):
        """Change a loan's status (admin)."""
        return loan_service.set_status(loan_id, data["status"])
