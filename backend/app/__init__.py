from flask import Flask

from app.cli import register_cli
from app.config import get_config
from app.errors import register_error_handlers
from app.extensions import init_extensions
from app.routes import register_routes


def create_app(env_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(env_name))

    from app import models  # noqa: F401 - registers models with SQLAlchemy's metadata

    init_extensions(app)
    register_routes(app)
    register_error_handlers(app)
    register_cli(app)

    return app
