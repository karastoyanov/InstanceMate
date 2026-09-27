from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        if isinstance(exc, HTTPException):
            # A normal 404/405/etc. - let Flask's default handling render it.
            return exc

        # In debug/testing, let Flask's normal handling surface the real
        # traceback. Otherwise, never leak exception details (which could
        # include instance URLs, stack frames, etc.) to the client - log
        # server-side and return a generic error.
        if app.debug or app.testing:
            raise exc

        app.logger.exception("Unhandled exception")
        return jsonify(error="Internal server error"), 500
