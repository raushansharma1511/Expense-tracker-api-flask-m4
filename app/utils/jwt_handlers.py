from flask import jsonify
from app.utils.logger import logger
from app.extensions import jwt


def register_jwt_error_handlers(app):
    """
    Register error handlers for JWT authentication.

    Args:
        jwt: The Flask-JWT-Extended instance
    """

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        logger.error("Token has expired, login again")
        return (
            jsonify({"error": "Token has expired, login again"}),
            401,
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        logger.error("Invalid token, signature verification failed")
        return (
            jsonify({"error": "Invalid token"}),
            401,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        logger.error("Authorization required, request does not contain an access token")
        return (
            jsonify(
                {"error": "Authorization required, Request does not contain a token"}
            ),
            401,
        )

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        logger.error("Token has been revoked, login again")
        return (
            jsonify({"error": "Token has been revoked, Please log in again"}),
            401,
        )

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {"error": "Fresh token required, The operation requires a fresh login"}
            ),
            401,
        )
