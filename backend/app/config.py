import os


class Config:
    SESSION_SECRET = os.environ.get("SESSION_SECRET", "changeme")
    SECRET_KEY = SESSION_SECRET
    DATABASE_URL = os.environ.get("DATABASE_URL")
    MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL")

    # Backend's own externally-reachable base URL, used to build the fixed
    # OAuth redirect_uri registered in the user's ServiceNow instance.
    APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://127.0.0.1:5000")
    # Frontend origin: allowed for CORS and used as the post-login redirect target.
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


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
