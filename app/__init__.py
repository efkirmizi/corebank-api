"""Application factory.

    from app import create_app
    app = create_app()               # env-driven config
    app = create_app("testing")      # explicit

Layering: api → services → repositories → db. Nothing below the api layer
imports Flask; the factory is the only place the layers are wired together.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from flask import Flask
from flask_cors import CORS

from app.api import register_blueprints
from app.api.errors import register_error_handlers
from app.config import BaseConfig, get_config
from app.db import init_pool
from app.extensions import api, jwt
from app.logging_config import configure_logging
from app.security import register_jwt_handlers


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)

    config = get_config(config_name)
    app.config.from_object(config)
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=config.JWT_ACCESS_TOKEN_EXPIRES_HOURS)

    configure_logging(app)
    _init_extensions(app, config)

    register_jwt_handlers(jwt)
    register_error_handlers(app)
    register_blueprints(api)

    app.logger.info("corebank-api started (env=%s)", config_name or "auto")
    return app


def _init_extensions(app: Flask, config: type[BaseConfig]) -> None:
    origins = [o.strip() for o in config.CORS_ORIGINS.split(",") if o.strip()]
    CORS(app, resources={r"/api/*": {"origins": origins or "*"}})

    jwt.init_app(app)
    api.init_app(app)

    # The connection pool is created eagerly so a bad DB config fails at boot,
    # not on the first request. Skipped under testing, where the test harness
    # rebinds the pool to an ephemeral database.
    if not app.config.get("TESTING"):
        init_pool(app.config)
        logging.getLogger(__name__).debug("connection pool initialized")
