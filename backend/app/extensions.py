from flask import Flask
from flask_cors import CORS


def init_extensions(app: Flask) -> None:
    CORS(app, origins=[app.config["FRONTEND_URL"]], supports_credentials=True)
