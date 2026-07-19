"""Customer-support ticket endpoints, including the top-resolvers report."""

from __future__ import annotations

from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint
from marshmallow import Schema, fields, validate

from app.security import admin_required, current_user, is_admin
from app.services import support_service
from app.services.exceptions import BadRequestError

blp = Blueprint("customer_support", __name__, description="Support tickets")

TICKET_STATUSES = ("OPEN", "IN_PROGRESS", "RESOLVED")


class TicketSchema(Schema):
    ticket_id = fields.String(dump_only=True)
    customer_id = fields.String()
    employee_id = fields.String(required=True)
    issue_description = fields.String(required=True)
    status = fields.String(dump_only=True)
    created_date = fields.DateTime(dump_only=True)
    resolved_date = fields.DateTime(dump_only=True, allow_none=True)


class TicketCreateSchema(Schema):
    # customer_id is honored only for admins; customers always file for themselves.
    customer_id = fields.String(load_default=None)
    employee_id = fields.String(required=True)
    issue_description = fields.String(required=True, validate=validate.Length(min=1))


class TicketStatusSchema(Schema):
    status = fields.String(required=True, validate=validate.OneOf(TICKET_STATUSES))


class TopResolverSchema(Schema):
    employee_id = fields.String()
    first_name = fields.String()
    last_name = fields.String()
    resolved_tickets = fields.Integer()


@blp.route("/")
class Tickets(MethodView):
    @admin_required
    @blp.response(200, TicketSchema(many=True))
    def get(self):
        """List all tickets (admin)."""
        return support_service.list_all()

    @jwt_required()
    @blp.arguments(TicketCreateSchema)
    @blp.response(201, TicketSchema)
    def post(self, data):
        """Open a ticket. Customers file for themselves; admins may name any customer."""
        actor = current_user()
        customer_id = data.get("customer_id") if is_admin() else actor["customer_id"]
        if not customer_id:
            raise BadRequestError("A customer_id is required")
        return support_service.create(customer_id, data["employee_id"], data["issue_description"])


@blp.route("/reports/top-resolvers")
class TopResolvers(MethodView):
    @admin_required
    @blp.response(200, TopResolverSchema(many=True))
    def get(self):
        """Employees tied for the most resolved tickets (admin)."""
        return support_service.top_resolvers()


@blp.route("/<ticket_id>")
class Ticket(MethodView):
    @jwt_required()
    @blp.response(200, TicketSchema)
    def get(self, ticket_id):
        """Fetch one ticket (owner or admin)."""
        return support_service.get(ticket_id, current_user())

    @admin_required
    @blp.response(204)
    def delete(self, ticket_id):
        """Delete a ticket (admin)."""
        support_service.delete(ticket_id)
        return ""


@blp.route("/<ticket_id>/status")
class TicketStatus(MethodView):
    @admin_required
    @blp.arguments(TicketStatusSchema)
    @blp.response(200, TicketSchema)
    def put(self, data, ticket_id):
        """Change a ticket's status (admin)."""
        return support_service.set_status(ticket_id, data["status"])
