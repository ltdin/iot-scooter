"""Flask entrypoint for the Master Pi core system."""

from flask import Flask, request
from werkzeug.exceptions import HTTPException

from master.api.routes import api_bp
from master.config import Config
from master.utils.response import error_response


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        return response

    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = app.make_default_options_response()
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            return response

    @app.get("/health")
    def health_check():
        return {"success": True, "message": "Master Pi API is running"}

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return error_response(error.description, error.code)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        return error_response(str(error), 500)

    return app


if __name__ == "__main__":
    create_app().run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG,
    )
