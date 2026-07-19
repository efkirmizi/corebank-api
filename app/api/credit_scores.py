"""Credit-score endpoints."""
from __future__ import annotations

from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint
from flask.views import MethodView
from marshmallow import Schema, fields, validate

from app.security import admin_required, current_user
from app.services import credit_score_service
from app.services.exceptions import BadRequestError

blp = Blueprint("credit_scores", __name__, description="Credit scores")


class CreditScoreSchema(Schema):
    credit_score_id = fields.String(dump_only=True)
    customer_id = fields.String(required=True)
    score = fields.Decimal(places=2, as_string=True, required=True)
    risk_category = fields.String(required=True, validate=validate.Length(max=50))
    computed_by_system = fields.Boolean(load_default=True)


class CreditScoreUpdateSchema(Schema):
    score = fields.Decimal(places=2, as_string=True)
    risk_category = fields.String(validate=validate.Length(max=50))
    computed_by_system = fields.Boolean()


@blp.route("/")
class CreditScores(MethodView):
    @admin_required
    @blp.response(200, CreditScoreSchema(many=True))
    def get(self):
        """List credit scores (admin)."""
        return credit_score_service.list_all()

    @admin_required
    @blp.arguments(CreditScoreSchema)
    @blp.response(201, CreditScoreSchema)
    def post(self, data):
        """Record a credit score (admin)."""
        return credit_score_service.create(data)


@blp.route("/<credit_score_id>")
class CreditScore(MethodView):
    @jwt_required()
    @blp.response(200, CreditScoreSchema)
    def get(self, credit_score_id):
        """Fetch one credit score (owner or admin)."""
        return credit_score_service.get(credit_score_id, current_user())

    @admin_required
    @blp.arguments(CreditScoreUpdateSchema)
    @blp.response(200, CreditScoreSchema)
    def put(self, data, credit_score_id):
        """Update a credit score (admin)."""
        if not data:
            raise BadRequestError("No fields to update")
        return credit_score_service.update(credit_score_id, data)

    @admin_required
    @blp.response(204)
    def delete(self, credit_score_id):
        """Delete a credit score (admin)."""
        credit_score_service.delete(credit_score_id)
        return ""
