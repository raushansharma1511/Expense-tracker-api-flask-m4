import uuid
from flask_restful import Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from flask import g
from app.extensions import db

from app.schemas.auth import (
    user_schema,
    login_schema,
    password_reset_request_schema,
    password_reset_confirm_schema,
)
from app.services.auth import (
    verify_user_by_token,
    authenticate_user,
    generate_tokens,
    send_password_reset_link,
    reset_password_with_token,
    prepare_user_creation,
)
from app.models.user import User
from app.utils.logger import logger
from app.utils.permissions import (
    authenticated_user,
)
from app.utils.tokens import TokenHandler
from app.utils.responses import validation_error_response
from app.utils.enums import UserRole


class SignupResource(Resource):
    def post(self):
        try:
            data = request.get_json()
            logger.info(f"Received signup request with data: {data}")

            user_data = user_schema.load(data)
            user_data.role = UserRole.USER

            token = prepare_user_creation(user_data)

            return {
                "message": f"User registration request accepted. Please check your email to verify your account.",
            }, 200

        except ValidationError as err:
            return validation_error_response(err)


class VerifyAccountResource(Resource):
    def get(self, token):
        logger.info(f"Received account verification request with token: {token}")
        try:
            if verify_user_by_token(token):
                return {"message": "Your account has been verified successfully"}, 200
        except ValidationError as e:
            return validation_error_response(e)


class LoginResource(Resource):
    def post(self):
        try:
            data = request.get_json() or {}
            logger.info(f"Received login request with data: {data}")

            data = login_schema.load(data)
            user = authenticate_user(data["username"], data["password"])
            tokens = generate_tokens(user)

            logger.info(f"User logged in successfully: {user.username}")
            return tokens, 200
        except ValidationError as e:
            return validation_error_response(e)


class LogoutResource(Resource):

    @authenticated_user
    def post(self):
        """Log out the current user by invalidating their token."""
        logger.info("Received logout request")
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.split(" ")[1] if auth_header.startswith("Bearer ") else None
        if not token:
            return {"error": "Invalid authorization header"}, 401

        TokenHandler.invalidate_access_token(token)
        return {"message": "Successfully logged out"}, 200


class RefreshAccessTokenResource(Resource):
    @jwt_required(refresh=True)
    def post(self):
        logger.info("Received refresh access token request")

        user_id = get_jwt_identity()
        user = db.session.get(User, uuid.UUID(user_id))

        if not user:
            return {"error": "User not found"}, 404
        # Create a new access token
        access_token = TokenHandler.generate_access_token(user, False)

        logger.info(f"Refreshed access token for user: {user.username}")
        return {"access_token": access_token}, 200


class PasswordResetRequestResource(Resource):
    """Resource for requesting a password reset link"""

    def post(self):
        try:
            data = request.get_json() or {}
            logger.info(f"Received password reset request with data: {data}")
            data = password_reset_request_schema.load(data)

            send_password_reset_link(data["email"])
            return {
                "message": "Check you gmail inbox, you will receive a password reset link shortly."
            }, 200

        except ValidationError as e:
            return validation_error_response(e)


class PasswordResetConfirmResource(Resource):
    """Resource for confirming a password reset with token from URL"""

    def post(self, token):
        try:
            # Validate the token from URL directly
            if not token:
                return {"error": "Token is missing"}, 400

            logger.info(
                f"Received password reset confirmation request with token: {token}"
            )

            # Get and validate request body without token requirement
            data = request.get_json() or {}
            data = password_reset_confirm_schema.load(data)

            # Validate token and reset password
            user = reset_password_with_token(token, data["password"])
            return {"message": "Password has been reset successfully"}, 200

        except ValidationError as e:
            return validation_error_response(e)
