import os


class Config:
    SESSION_SECRET = os.environ.get("SESSION_SECRET", "changeme")
    DATABASE_URL = os.environ.get("DATABASE_URL")
    MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL")


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    DEBUG = False


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(env_name: str | None = None) -> type[Config]:
    env_name = env_name or os.environ.get("FLASK_ENV", "development")
    return CONFIG_BY_NAME.get(env_name, DevelopmentConfig)
