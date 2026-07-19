"""Card endpoints."""

from __future__ import annotations

from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint
from marshmallow import Schema, fields, validate

from app.security import admin_required, current_user
from app.services import card_service

blp = Blueprint("cards", __name__, description="Payment cards")

CARD_TYPES = ("DEBIT", "CREDIT")
CARD_STATUSES = ("ACTIVE", "BLOCKED", "EXPIRED")


class CardSchema(Schema):
    card_id = fields.String(dump_only=True)
    account_id = fields.String(required=True)
    card_type = fields.String(validate=validate.OneOf(CARD_TYPES))
    card_number = fields.String(dump_only=True)  # masked by the repository
    expiration_date = fields.Date()
    status = fields.String(validate=validate.OneOf(CARD_STATUSES))


class CardCreateSchema(Schema):
    account_id = fields.String(required=True)
    card_type = fields.String(required=True, validate=validate.OneOf(CARD_TYPES))
    card_number = fields.String(required=True, load_only=True, validate=validate.Length(equal=16))
    expiration_date = fields.Date(required=True)
    cvv = fields.String(required=True, load_only=True, validate=validate.Length(min=3, max=3))
    status = fields.String(load_default="ACTIVE", validate=validate.OneOf(CARD_STATUSES))


class CardStatusSchema(Schema):
    status = fields.String(required=True, validate=validate.OneOf(CARD_STATUSES))


@blp.route("/")
class Cards(MethodView):
    @admin_required
    @blp.response(200, CardSchema(many=True))
    def get(self):
        """List cards (admin)."""
        return card_service.list_all()

    @admin_required
    @blp.arguments(CardCreateSchema)
    @blp.response(201, CardSchema)
    def post(self, data):
        """Issue a card (admin)."""
        return card_service.create(data)


@blp.route("/<card_id>")
class Card(MethodView):
    @jwt_required()
    @blp.response(200, CardSchema)
    def get(self, card_id):
        """Fetch one card (owner or admin)."""
        return card_service.get(card_id, current_user())

    @admin_required
    @blp.response(204)
    def delete(self, card_id):
        """Delete a card (admin)."""
        card_service.delete(card_id)
        return ""


@blp.route("/<card_id>/status")
class CardStatus(MethodView):
    @jwt_required()
    @blp.arguments(CardStatusSchema)
    @blp.response(200, CardSchema)
    def put(self, data, card_id):
        """Block or unblock a card (owner or admin)."""
        return card_service.set_status(card_id, data["status"], current_user())
