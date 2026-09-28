"""PocketSmart AI Flask application."""

from __future__ import annotations

from flask import Flask, jsonify
from flask_cors import CORS

from pocketsmart.config import FLASK_PORT, FLASK_SECRET_KEY
from pocketsmart.models.schemas import ValidationError
from pocketsmart.routes.api import api_bp
from pocketsmart.routes.pages import pages_bp


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config["SECRET_KEY"] = FLASK_SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
    CORS(app, supports_credentials=True)
    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp)

    @app.errorhandler(ValidationError)
    def handle_validation(exc: ValidationError):
        return jsonify({"error": str(exc), "code": exc.code}), 400

    @app.errorhandler(413)
    def too_large(_e):
        return jsonify({"error": "Upload is too large.", "code": "file_too_large"}), 413

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)
