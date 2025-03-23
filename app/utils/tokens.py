import secrets
from datetime import timedelta

from flask_jwt_extended import create_access_token, create_refresh_token
from flask import current_app

from app.models.auth import ActiveAccessToken
from app.extensions import db, redis_client
from app.utils.logger import logger


class TokenHandler:
    """
    Utility class to handle token-related operations for Flask.
    """

    @staticmethod
    def generate_access_token(user, fresh):
        """Generate access token for a user"""

        additional_claims = {
            "role": user.role.value if hasattr(user.role, "value") else str(user.role)
        }
        access_token = create_access_token(
            identity=str(user.id),
            fresh=fresh,  # This is not a fresh login
            additional_claims=additional_claims,
            expires_delta=timedelta(
                seconds=current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
            ),
        )
        token_entry = ActiveAccessToken(access_token=access_token, user_id=user.id)
        db.session.add(token_entry)
        db.session.commit()
        return access_token

    @staticmethod
    def generate_refresh_token(user):
        """Generate refresh token for a user"""

        additional_claims = {
            "role": user.role.value if hasattr(user.role, "value") else str(user.role)
        }

        refresh_token = create_refresh_token(
            identity=str(user.id),
            additional_claims=additional_claims,
            expires_delta=timedelta(
                seconds=current_app.config["JWT_REFRESH_TOKEN_EXPIRES"]
            ),
        )
        return refresh_token

    @staticmethod
    def invalidate_access_token(token):
        """
        Invalidate a specific access token.
        """
        token_entry = ActiveAccessToken.query.filter_by(access_token=token).first()
        if token_entry:
            db.session.delete(token_entry)
            db.session.commit()
            logger.info(
                f"Logout successfully and Invalidated token for user: {token_entry.user.username}"
            )

    @staticmethod
    def invalidate_user_access_tokens(user_id):
        """
        Invalidate all active tokens for a given user.
        """
        tokens = ActiveAccessToken.query.filter_by(user_id=user_id).all()
        for token in tokens:
            db.session.delete(token)
        db.session.commit()
        logger.info(f"Invalidated all tokens for user: {user_id}")

    @staticmethod
    def generate_password_reset_token():
        """Generate a secure random token for password reset."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def store_reset_token(user_id, token):  # 15 minutes default
        """Store a password reset token in Redis with expiration."""
        key = f"password_reset:{token}"
        redis_client.setex(
            key, current_app.config["PASSWORD_RESET_LINK_VALIDITY"], str(user_id)
        )

        # Also store a rate limiting key to prevent too many requests
        rate_limit_key = f"password_reset_link_rate_limit:{user_id}"
        if not redis_client.exists(rate_limit_key):
            redis_client.setex(
                rate_limit_key,
                current_app.config["PASSWORD_RESET_LINK_SEND_RATE_LIMIT"],
                "1",
            )

    @staticmethod
    def verify_reset_token(token):
        """Verify a password reset token and return the associated user ID."""
        key = f"password_reset:{token}"
        user_id = redis_client.get(key)

        if user_id:
            # Delete the token so it can't be used again
            redis_client.delete(key)
            return user_id

        return None
