from flask import Flask

from app.routes.account import account_bp
from app.routes.health import health_bp
from app.routes.llm_profiles import profiles_bp as llm_profiles_bp
from app.routes.servicenow_profiles import profiles_bp as servicenow_profiles_bp


def register_routes(app: Flask) -> None:
    app.register_blueprint(health_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(servicenow_profiles_bp)
    app.register_blueprint(llm_profiles_bp)
