"""Branch endpoints, including the branch-conditions report."""

from __future__ import annotations

from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, fields, validate

from app.security import admin_required
from app.services import branch_service
from app.services.exceptions import BadRequestError

blp = Blueprint("branches", __name__, description="Branches")


class BranchSchema(Schema):
    branch_id = fields.String(dump_only=True)
    branch_name = fields.String(required=True)
    address_line1 = fields.String(required=True)
    address_line2 = fields.String(allow_none=True)
    city = fields.String(required=True)
    zip_code = fields.String(required=True)
    phone_number = fields.String(required=True, validate=validate.Length(max=15))


class BranchUpdateSchema(Schema):
    branch_name = fields.String()
    address_line1 = fields.String()
    address_line2 = fields.String(allow_none=True)
    city = fields.String()
    zip_code = fields.String()
    phone_number = fields.String(validate=validate.Length(max=15))


class BranchConditionsArgs(Schema):
    min_employees = fields.Integer(load_default=5, validate=validate.Range(min=0))
    min_accounts = fields.Integer(load_default=3, validate=validate.Range(min=0))


class BranchConditionsResult(Schema):
    branch_name = fields.String()
    employee_count = fields.Integer()
    account_count = fields.Integer()


@blp.route("/")
class Branches(MethodView):
    @admin_required
    @blp.response(200, BranchSchema(many=True))
    def get(self):
        """List branches (admin)."""
        return branch_service.list_all()

    @admin_required
    @blp.arguments(BranchSchema)
    @blp.response(201, BranchSchema)
    def post(self, data):
        """Create a branch (admin)."""
        return branch_service.create(data)


@blp.route("/reports/conditions")
class BranchConditions(MethodView):
    @admin_required
    @blp.arguments(BranchConditionsArgs, location="query")
    @blp.response(200, BranchConditionsResult(many=True))
    def get(self, args):
        """Branches above employee and account thresholds (admin)."""
        return branch_service.with_conditions(args["min_employees"], args["min_accounts"])


@blp.route("/<branch_id>")
class Branch(MethodView):
    @admin_required
    @blp.response(200, BranchSchema)
    def get(self, branch_id):
        """Fetch one branch (admin)."""
        return branch_service.get(branch_id)

    @admin_required
    @blp.arguments(BranchUpdateSchema)
    @blp.response(200, BranchSchema)
    def put(self, data, branch_id):
        """Update a branch (admin)."""
        if not data:
            raise BadRequestError("No fields to update")
        return branch_service.update(branch_id, data)

    @admin_required
    @blp.response(204)
    def delete(self, branch_id):
        """Delete a branch (admin)."""
        branch_service.delete(branch_id)
        return ""
