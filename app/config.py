"""Application configuration.

Config is read from the environment so no secrets live in the repository.
Production refuses to start if required secrets are missing.
"""

from __future__ import annotations

import os


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


class BaseConfig:
    # --- Flask / API ---
    API_TITLE = "corebank-api"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/docs"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    OPENAPI_JSON_PATH = "openapi.json"
    PROPAGATE_EXCEPTIONS = True
    API_SPEC_OPTIONS = {
        "info": {
            "description": (
                "Core banking REST API — accounts, cards, loans, transfers, and "
                "reporting. Hand-written SQL behind a layered service architecture. "
                "Authenticate at `POST /api/v1/auth/login`, then send "
                "`Authorization: Bearer <token>`."
            ),
        },
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            }
        },
        "security": [{"BearerAuth": []}],
    }

    # --- JWT ---
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES_HOURS = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "1"))

    # --- Database ---
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "bank")
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))

    # --- CORS ---
    # Comma-separated allowlist. "*" allows all (development only).
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    TESTING = False
    DEBUG = False

    @classmethod
    def validate(cls) -> None:
        """Raise if the configuration is unsafe to run. Overridden per env."""


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    # >= 32 bytes so HS256 does not warn; still not a production secret.
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-insecure-secret-key-not-for-production")


class TestingConfig(BaseConfig):
    TESTING = True
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "test-only-secret-key-at-least-32-bytes-long")
    DB_NAME = os.getenv("DB_NAME", "bank_test")


class ProductionConfig(BaseConfig):
    @classmethod
    def validate(cls) -> None:
        missing = [
            name
            for name in ("JWT_SECRET_KEY", "DB_PASSWORD", "DB_NAME", "DB_USER", "DB_HOST")
            if not getattr(cls, name)
        ]
        if missing:
            raise RuntimeError(
                "Refusing to start: missing required environment variables: " + ", ".join(missing)
            )
        if cls.CORS_ORIGINS == "*":
            raise RuntimeError("Refusing to start: CORS_ORIGINS must not be '*' in production.")


_CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None) -> type[BaseConfig]:
    name = (name or os.getenv("APP_ENV", "development")).lower()
    config = _CONFIGS.get(name, DevelopmentConfig)
    config.validate()
    return config
