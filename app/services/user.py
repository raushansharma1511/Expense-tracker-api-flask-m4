from flask import request, current_app
import uuid
import secrets
import string

from marshmallow import ValidationError
from app.extensions import db, redis_client
from app.models.user import User, ParentChildRelation
from app.utils.logger import logger
from app.tasks.user import send_email_change_otps

from app.tasks.user import soft_delete_user_related_objects
from app.utils.tokens import TokenHandler
from app.utils.enums import UserRole
from app.models.auth import ActiveAccessToken


def request_email_change(user, new_email):
    """
    Request an email change with separate OTP verification for each email.
    """
    try:
        # Use the same redis_key for both OTPs and rate limiting
        redis_key = f"email_change:{user.id}"

        # Check if there's an existing pending email change request (rate limiting)
        if redis_client.exists(redis_key):
            time_remaining = redis_client.ttl(redis_key)
            minutes_remaining = int(time_remaining / 60) + 1
            raise ValidationError(
                f"Please wait {minutes_remaining} minutes before requesting another email change"
            )

        # Generate two different OTPs - 6 digit numeric codes
        current_email_otp = "".join(secrets.choice(string.digits) for _ in range(6))
        new_email_otp = "".join(secrets.choice(string.digits) for _ in range(6))

        OTP_VALID_FOR = current_app.config["OTP_VALID_FOR"]

        # Store OTPs in Redis with expiration (eg. 15 minutes)
        redis_client.setex(
            redis_key, OTP_VALID_FOR, f"{new_email}:{current_email_otp}:{new_email_otp}"
        )

        # Send different OTPs to each email address asynchronously
        send_email_change_otps.delay(
            user.email, new_email, current_email_otp, new_email_otp
        )

        logger.info(
            f"Email change OTPs sent for user {user.id}: {user.email} -> {new_email}"
        )
        return True

    except ValidationError as e:
        # Pass through validation errors
        raise
    except Exception as e:
        logger.error(f"Error requesting email change: {str(e)}", exc_info=True)
        raise Exception(
            f"An error occurred while processing the email change request: {str(e)}"
        )


def confirm_email_change(user, current_email_otp, new_email_otp):
    """
    Confirm email change with separate OTPs for each email.
    - verify the otps send on the both email.
    """
    try:
        # Get stored data from Redis
        redis_key = f"email_change:{user.id}"
        stored_data = redis_client.get(redis_key)

        if not stored_data:
            raise ValidationError("Otp is expired")

        new_email, stored_current_otp, stored_new_otp = stored_data.split(":")

        if current_email_otp != stored_current_otp and new_email_otp != stored_new_otp:
            raise ValidationError("Both current and new email OTPs are incorrect.")

        if current_email_otp != stored_current_otp:
            raise ValidationError("Invalid current email otp")

        if new_email_otp != stored_new_otp:
            raise ValidationError("Invalid new email otp.")

        # Update email
        user.email = new_email
        db.session.commit()

        # Delete Redis key
        redis_client.delete(redis_key)

        logger.info(f"Email changed for user {user.id} to {new_email}")
        return True

    except ValidationError as e:
        # Pass through validation errors
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error confirming email change: {str(e)}", exc_info=True)
        raise Exception(f"Failed to change email: {str(e)}")


def generate_admin_email_change_token(user, new_email):
    """
    Generate a token for admin-initiated email change, invalidate all previous tokens,
    store the new token in Redis, and track it in a set.
    """
    # Generate a random token
    token = secrets.token_urlsafe(32)
    redis_key = f"admin_email_change:{token}"
    user_active_token_key = f"user_active_email_change:{user.id}"

    # Rate limit check
    redis_ttl_key = f"admin_email_change_ttl:{user.id}"
    if redis_client.exists(redis_ttl_key):
        time_remaining = redis_client.ttl(redis_ttl_key)
        minutes_remaining = int(time_remaining / 60) + 1
        raise ValidationError(
            f"Please wait {minutes_remaining} minutes before requesting another email change"
        )

    # Invalidate all previous tokens
    previous_token = redis_client.get(user_active_token_key)
    if previous_token:
        old_token_key = f"admin_email_change:{previous_token}"
        redis_client.delete(old_token_key)
        logger.info(
            f"Invalidated previous email change token: {old_token_key} for user {user.id}"
        )

    EMAIL_CHANGE_TOKEN_VALIDITY = current_app.config["EMAIL_CHANGE_TOKEN_VALIDITY"]

    # Store the new token with user ID and new email
    redis_client.setex(redis_key, EMAIL_CHANGE_TOKEN_VALIDITY, f"{user.id}:{new_email}")

    # Add the new token to the set
    redis_client.setex(user_active_token_key, EMAIL_CHANGE_TOKEN_VALIDITY, token)

    # Set rate limit
    redis_client.setex(
        redis_ttl_key, current_app.config["EMAIL_CHANGE_TOKEN_RESEND"], "1"
    )

    logger.info(
        f"admin-initiated email change token generated for user {user.id}: {user.email} -> {new_email}, "
        f"previous token invalidated."
    )
    return token


def verify_admin_email_change_token(token):
    """
    Verify a admin-initiated email change token and clean up.
    """

    redis_key = f"admin_email_change:{token}"
    stored_data = redis_client.get(redis_key)

    if not stored_data:
        logger.warning(f"Invalid or expired token: {token}")
        return None, None

    # Parse the stored data
    user_id, new_email = stored_data.split(":")

    redis_client.delete(redis_key)  # Delete the used token
    redis_client.delete(
        f"user_active_email_change:{user_id}"
    )  # Delete the active token reference.

    logger.info(f"Verified token {token} for user {user_id}, token invalidated")
    return user_id, new_email


def logout_other_sessions(user):
    """
    Invalidate all active tokens for a given user except the current one.
    """
    # Get current token
    auth_header = request.headers.get("Authorization", "")
    current_token = (
        auth_header.split(" ")[1] if auth_header.startswith("Bearer ") else None
    )
    # Invalidate all tokens except current one
    tokens = ActiveAccessToken.query.filter_by(user_id=user.id).all()
    for token in tokens:
        if token.access_token != current_token:
            db.session.delete(token)
    db.session.commit()
    logger.info(f"Invalidated all other tokens for user: {user.id}")


def delete_user_account(current_user, target_user, password=None):
    """
    Delete a user account (soft delete) and its related things.
    """
    try:
        logger.info(f"Starting deletion process for user {target_user.id}")

        if target_user.role.value == UserRole.USER.value:
            child_user = target_user.get_child()

            if child_user:
                child_user_id = child_user.id
                logger.info(f"Deleting child user {child_user_id}")
                child_user.is_deleted = True

                relation = ParentChildRelation.query.filter_by(
                    child_id=child_user_id
                ).first()
                relation.is_deleted = True
                logger.info(f"Deleting parent-child relation {relation.id}")

                soft_delete_user_related_objects.delay(str(child_user_id))

        target_user.is_deleted = True
        db.session.commit()

        soft_delete_user_related_objects.delay(str(target_user.id))

        logger.info(
            f"User account deleted - ID: {target_user.id}, Email: {target_user.email}, "
            + f"Deleted by: {current_user.id}"
        )

        return True

    except ValidationError as e:
        # Pass through validation errors
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting user account: {str(e)}", exc_info=True)
        raise Exception(f"Failed to delete user account: {str(e)}")
