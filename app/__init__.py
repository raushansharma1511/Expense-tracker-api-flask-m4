import uuid
from flask import Flask, request
from marshmallow.exceptions import ValidationError

from app.config import Config  # Import configuration settings
from app.extensions import db, migrate, bcrypt, jwt, mail, init_limiter, limiter
from app.urls import register_blueprints
from app.utils.jwt_handlers import register_jwt_error_handlers
from app.celery_app import make_celery
from app.utils.exception_handler import handle_error


def create_app(test_config=None):
    """Factory function to create and configure the Flask application"""
    app = Flask(__name__)  # Create Flask app instance

    if test_config:
        app.config.from_object(test_config)
    else:
        app.config.from_object(Config)  # Load configuration from config.py

    app.config["PROPAGATE_EXCEPTIONS"] = True

    # Initialize Flask extensions
    db.init_app(app)  # Initialize SQLAlchemy
    migrate.init_app(app, db)  # Initialize Flask-Migrate
    mail.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)  # Initialize JWT authentication

    # Register JWT error handlers
    register_jwt_error_handlers(app)

    # Register Blueprints (URLs)
    register_blueprints(app)

    app.celery = make_celery(app)
    handle_error(app)

    @app.before_request
    def validate_uuid_params():
        # Check if view_args is populated and has an 'id' key
        if request.view_args and "id" in request.view_args:
            id_value = request.view_args["id"]
            try:
                uuid.UUID(id_value)  # Validate UUID format
            except ValueError:
                return {
                    "error": f"Invalid id format, it must be a UUID: {id_value}"
                }, 400

    return app


# importing all the models
from app import models
