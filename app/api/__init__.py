"""HTTP layer: thin flask-smorest blueprints, one module per resource.

Every resource blueprint is registered here under the ``/api/v1`` prefix. Health
probes are mounted at the root so orchestrators can reach them without a version.
"""
from __future__ import annotations

from flask_smorest import Api

V1 = "/api/v1"


def register_blueprints(api: Api) -> None:
    # Imported lazily so the app factory controls import order.
    from .accounts import blp as accounts_blp
    from .auth import blp as auth_blp
    from .branches import blp as branches_blp
    from .cards import blp as cards_blp
    from .credit_scores import blp as credit_scores_blp
    from .customer_support import blp as support_blp
    from .customers import blp as customers_blp
    from .employees import blp as employees_blp
    from .health import blp as health_blp
    from .loan_payments import blp as loan_payments_blp
    from .loans import blp as loans_blp
    from .transactions import blp as transactions_blp
    from .users import blp as users_blp

    api.register_blueprint(health_blp)
    api.register_blueprint(auth_blp, url_prefix=f"{V1}/auth")
    api.register_blueprint(users_blp, url_prefix=f"{V1}/users")
    api.register_blueprint(customers_blp, url_prefix=f"{V1}/customers")
    api.register_blueprint(accounts_blp, url_prefix=f"{V1}/accounts")
    api.register_blueprint(cards_blp, url_prefix=f"{V1}/cards")
    api.register_blueprint(branches_blp, url_prefix=f"{V1}/branches")
    api.register_blueprint(employees_blp, url_prefix=f"{V1}/employees")
    api.register_blueprint(loans_blp, url_prefix=f"{V1}/loans")
    api.register_blueprint(loan_payments_blp, url_prefix=f"{V1}/loan-payments")
    api.register_blueprint(transactions_blp, url_prefix=f"{V1}/transactions")
    api.register_blueprint(credit_scores_blp, url_prefix=f"{V1}/credit-scores")
    api.register_blueprint(support_blp, url_prefix=f"{V1}/support-tickets")
