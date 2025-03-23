import redis
from flask import jsonify, current_app
from marshmallow.exceptions import ValidationError
from app.utils.logger import logger
from werkzeug.exceptions import Forbidden


def handle_error(app):
    """Register global exception handlers for all types of exceptions"""

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle Marshmallow ValidationError (e.g., schema validation failures)"""
        if isinstance(error.messages, dict):
            formatted_errors = {
                field: messages[0] if isinstance(messages, list) else messages
                for field, messages in error.messages.items()
            }
        elif isinstance(error.messages, list):
            formatted_errors = error.messages[0] if len(error.messages) > 0 else "error"

        logger.warning(f"Validation error: {formatted_errors}")
        return {"error": formatted_errors}, 400

    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 Not Found errors"""
        logger.info(f"Resource not found: {str(error)}")
        return {
            "error": "The requested resource was not found",
        }, 404

    @app.errorhandler(403)
    def handle_forbidden(error):
        """Handle 403 Forbidden errors"""
        logger.info(f"Permission denied: {str(error)}")
        return {
            "error": "Forbidden, you do not have permission to access this resource",
        }, 403

    @app.errorhandler(401)
    def handle_unauthorized(error):
        """Handle 401 Unauthorized errors (e.g., JWT issues)"""
        logger.info(f"Unauthorized access: {str(error)}")
        return {"error": "Unauthorized, Authentication required"}, 401

    # Handle Redis connection errors
    @app.errorhandler(redis.RedisError)
    def handle_redis_error(e):
        logger.error(f"Redis error: {str(e)}", exc_info=True)

        # In production, don't expose specific Redis errors to clients
        if current_app.config.get("FLASK_ENV") == "production":
            response = {
                "error": "A temporary server issue occurred. Please try again later."
            }
        else:
            # In development, include more details
            response = {"error": "Redis connection error", "details": str(e)}

        return jsonify(response), 503

    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Handle all other unhandled exceptions"""
        logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
        return {
            "error": "Internal Server Error",
            "detail": str(error),
        }, 500
