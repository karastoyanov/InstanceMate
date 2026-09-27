import os
from datetime import timedelta
from typing import ClassVar


class Config:
    SESSION_SECRET = os.environ.get("SESSION_SECRET", "changeme")
    SECRET_KEY = SESSION_SECRET
    # Falls back to a local SQLite file so the app boots with zero setup;
    # set DATABASE_URL (see .env.example) to point at real Postgres.
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///dev.db")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_ENGINE_OPTIONS: ClassVar[dict] = {"pool_pre_ping": True}
    MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL")

    # Backend's own externally-reachable base URL, used to build the fixed
    # OAuth redirect_uri registered in the user's ServiceNow instance.
    # Uses the same hostname as FRONTEND_URL (localhost, not 127.0.0.1) so
    # the session cookie is same-site across the OAuth redirect round-trip.
    APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:5000")
    # Frontend origin: allowed for CORS and used as the post-login redirect target.
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False

    # Absolute lifetime of an established ServiceNow connection, regardless
    # of how long-lived the underlying OAuth token/refresh token is.
    SESSION_LIFETIME_SECONDS = int(
        os.environ.get("SESSION_LIFETIME_SECONDS", str(12 * 60 * 60))
    )
    # How long an in-progress OAuth authorization attempt (after /login,
    # before /callback) stays valid.
    PENDING_AUTHORIZATION_LIFETIME_SECONDS = int(
        os.environ.get("PENDING_AUTHORIZATION_LIFETIME_SECONDS", str(10 * 60))
    )
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=SESSION_LIFETIME_SECONDS)


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    # In-memory SQLite so tests don't need a real Postgres instance running.
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(env_name: str | None = None) -> type[Config]:
    env_name = env_name or os.environ.get("FLASK_ENV", "development")
    return CONFIG_BY_NAME.get(env_name, DevelopmentConfig)
