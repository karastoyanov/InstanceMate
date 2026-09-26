from flask import Flask

from app.config import get_config
from app.routes import register_routes


def create_app(env_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(env_name))

    register_routes(app)

    return app
