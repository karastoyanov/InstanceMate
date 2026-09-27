from flask import Flask

from app.routes.account import account_bp
from app.routes.health import health_bp
from app.routes.servicenow_profiles import profiles_bp


def register_routes(app: Flask) -> None:
    app.register_blueprint(health_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(profiles_bp)
