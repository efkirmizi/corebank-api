"""Employee endpoints. Admin-managed."""

from __future__ import annotations

from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, fields, validate

from app.security import admin_required
from app.services import employee_service
from app.services.exceptions import BadRequestError

blp = Blueprint("employees", __name__, description="Employees (admin)")


class EmployeeSchema(Schema):
    employee_id = fields.String(dump_only=True)
    branch_id = fields.String(required=True)
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    position = fields.String(required=True)
    hire_date = fields.DateTime(required=True)
    phone_number = fields.String(required=True, validate=validate.Length(max=15))
    email = fields.Email(required=True)


class EmployeeUpdateSchema(Schema):
    branch_id = fields.String()
    first_name = fields.String()
    last_name = fields.String()
    position = fields.String()
    hire_date = fields.DateTime()
    phone_number = fields.String(validate=validate.Length(max=15))
    email = fields.Email()


@blp.route("/")
class Employees(MethodView):
    @admin_required
    @blp.response(200, EmployeeSchema(many=True))
    def get(self):
        """List employees (admin)."""
        return employee_service.list_all()

    @admin_required
    @blp.arguments(EmployeeSchema)
    @blp.response(201, EmployeeSchema)
    def post(self, data):
        """Create an employee (admin)."""
        return employee_service.create(data)


@blp.route("/<employee_id>")
class Employee(MethodView):
    @admin_required
    @blp.response(200, EmployeeSchema)
    def get(self, employee_id):
        """Fetch one employee (admin)."""
        return employee_service.get(employee_id)

    @admin_required
    @blp.arguments(EmployeeUpdateSchema)
    @blp.response(200, EmployeeSchema)
    def put(self, data, employee_id):
        """Update an employee (admin)."""
        if not data:
            raise BadRequestError("No fields to update")
        return employee_service.update(employee_id, data)

    @admin_required
    @blp.response(204)
    def delete(self, employee_id):
        """Delete an employee (admin)."""
        employee_service.delete(employee_id)
        return ""
