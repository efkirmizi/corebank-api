"""Loan-payment endpoints. Admin-managed."""
from __future__ import annotations

from flask_smorest import Blueprint
from flask.views import MethodView
from marshmallow import Schema, fields, validate

from app.security import admin_required
from app.services import loan_payment_service

from ._fields import money

blp = Blueprint("loan_payments", __name__, description="Loan payments (admin)")


class LoanPaymentSchema(Schema):
    loan_payment_id = fields.String(dump_only=True)
    loan_id = fields.String(required=True)
    payment_date = fields.DateTime()
    payment_amount = money(required=True, validate=validate.Range(min=0, min_inclusive=False))
    remaining_balance = money(allow_none=True)


class LoanPaymentCreateSchema(Schema):
    loan_id = fields.String(required=True)
    payment_amount = money(required=True, validate=validate.Range(min=0, min_inclusive=False))
    remaining_balance = money(allow_none=True, load_default=None)
    payment_date = fields.DateTime(load_default=None)


@blp.route("/")
class LoanPayments(MethodView):
    @admin_required
    @blp.response(200, LoanPaymentSchema(many=True))
    def get(self):
        """List loan payments (admin)."""
        return loan_payment_service.list_all()

    @admin_required
    @blp.arguments(LoanPaymentCreateSchema)
    @blp.response(201, LoanPaymentSchema)
    def post(self, data):
        """Record a loan payment (admin)."""
        payload = {k: v for k, v in data.items() if v is not None}
        return loan_payment_service.create(payload)


@blp.route("/by-loan/<loan_id>")
class LoanPaymentsByLoan(MethodView):
    @admin_required
    @blp.response(200, LoanPaymentSchema(many=True))
    def get(self, loan_id):
        """List payments for a loan (admin)."""
        return loan_payment_service.list_by_loan(loan_id)


@blp.route("/<loan_payment_id>")
class LoanPayment(MethodView):
    @admin_required
    @blp.response(200, LoanPaymentSchema)
    def get(self, loan_payment_id):
        """Fetch one loan payment (admin)."""
        return loan_payment_service.get(loan_payment_id)

    @admin_required
    @blp.response(204)
    def delete(self, loan_payment_id):
        """Delete a loan payment (admin)."""
        loan_payment_service.delete(loan_payment_id)
        return ""
