"""Customer endpoints."""
from __future__ import annotations

from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint
from flask.views import MethodView
from marshmallow import Schema, fields, validate

from app.security import admin_required, current_user
from app.services import customer_service
from app.services.exceptions import BadRequestError

from ._fields import money

blp = Blueprint("customers", __name__, description="Customers")


class CustomerSchema(Schema):
    customer_id = fields.String(dump_only=True)
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    date_of_birth = fields.Date(required=True)
    phone_number = fields.String(required=True, validate=validate.Length(max=15))
    email = fields.Email(required=True)
    address_line1 = fields.String(required=True)
    address_line2 = fields.String(allow_none=True)
    city = fields.String(required=True)
    zip_code = fields.String(required=True)
    wage_declaration = money()


class CustomerUpdateSchema(Schema):
    first_name = fields.String()
    last_name = fields.String()
    phone_number = fields.String(validate=validate.Length(max=15))
    email = fields.Email()
    address_line1 = fields.String()
    address_line2 = fields.String(allow_none=True)
    city = fields.String()
    zip_code = fields.String()
    wage_declaration = money()


@blp.route("/")
class Customers(MethodView):
    @admin_required
    @blp.response(200, CustomerSchema(many=True))
    def get(self):
        """List customers (admin)."""
        return customer_service.list_all()

    @admin_required
    @blp.arguments(CustomerSchema)
    @blp.response(201, CustomerSchema)
    def post(self, data):
        """Create a customer (admin)."""
        return customer_service.create(data)


@blp.route("/<customer_id>")
class Customer(MethodView):
    @jwt_required()
    @blp.response(200, CustomerSchema)
    def get(self, customer_id):
        """Fetch one customer (owner or admin)."""
        return customer_service.get(customer_id, current_user())

    @jwt_required()
    @blp.arguments(CustomerUpdateSchema)
    @blp.response(200, CustomerSchema)
    def put(self, data, customer_id):
        """Update a customer (owner or admin)."""
        if not data:
            raise BadRequestError("No fields to update")
        return customer_service.update(customer_id, data, current_user())

    @admin_required
    @blp.response(204)
    def delete(self, customer_id):
        """Delete a customer (admin)."""
        customer_service.delete(customer_id)
        return ""
