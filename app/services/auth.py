import uuid, os
import json
import re
from flask import url_for, current_app
from marshmallow.exceptions import ValidationError
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.utils.logger import logger
from app.utils.tokens import TokenHandler
from app.tasks.auth import send_verification_email, send_password_reset_email
from app.models.user import ParentChildRelation
from app.models.wallet import Wallet
from app.utils.constants import DEFAULT_WALLET_NAME
from app.utils.enums import UserRole
from app.extensions import db, bcrypt, redis_client


def create_user(user_data):
    new_user = User(
        username=user_data.get("username"),
        email=user_data.get("email"),
        password=user_data.get("password"),
        name=user_data.get("name"),
        role=user_data.get("role"),
        is_verified=True,
    )

    # Add optional fields
    if "date_of_birth" in user_data and user_data.get("date_of_birth"):
        new_user.date_of_birth = user_data.get("date_of_birth")

    if "gender" in user_data and user_data.get("gender"):
        new_user.gender = user_data.get("gender")

    # Add to database
    db.session.add(new_user)
    db.session.flush()  # Get ID assigned

    if new_user.role != UserRole.ADMIN:
        default_wallet = Wallet(name=DEFAULT_WALLET_NAME, user_id=new_user.id)
        db.session.add(default_wallet)

    # Create parent-child relationship if needed
    if "parent_id" in user_data and user_data.get("parent_id"):
        relation = ParentChildRelation(
            parent_id=uuid.UUID(user_data.get("parent_id")), child_id=new_user.id
        )
        db.session.add(relation)

    db.session.commit()

    return new_user


def prepare_user_creation(user, parent_user=None):

    # Prepare data for Redis
    user_dict = {
        "username": user.username,
        "email": user.email,
        "password": bcrypt.generate_password_hash(user.password).decode("utf-8"),
        "name": user.name,
        "role": user.role.value,
        "is_verified": False,
    }
    # Add optional fields
    if parent_user:
        user_dict["parent_id"] = str(parent_user.id)

    if hasattr(user, "date_of_birth") and user.date_of_birth:
        user_dict["date_of_birth"] = user.date_of_birth.isoformat()

    if hasattr(user, "gender") and user.gender:
        user_dict["gender"] = (
            user.gender.value if hasattr(user.gender, "value") else user.gender
        )

    return initiate_verification(user_dict)


def initiate_verification(data, endpoint="auth.verify-user"):

    email = data.get("email")

    signup_key = f"user_signup:{email}"
    if redis_client.exists(signup_key):
        ttl = redis_client.ttl(signup_key)
        minutes_remaining = int(ttl / 60) + 1
        logger.warning(f"Registration already in progress for: {email}")
        raise ValidationError(
            f"User Registration of user with email {email} is alreday in progress, check your email for verification or try again after {minutes_remaining} minutes."
        )

    token = str(uuid.uuid4())
    verification_key = f"verification_token:{token}"
    verification_ttl = current_app.config.get("ACCCOUNT_VERIFICATION_LINK_VALIDITY")

    # storing the data to the redis for verifcation
    redis_client.setex(verification_key, verification_ttl, json.dumps(data))
    # storing the ttl for multiple requests
    redis_client.setex(signup_key, verification_ttl, token)

    verify_url = url_for(endpoint, token=token, _external=True)

    send_verification_email.delay(email, verify_url)

    logger.info(f"Account verification email sent to: {email}")
    return token


def verify_user_by_token(token):
    """Verify user using Redis-stored token."""

    verification_key = f"verification_token:{token}"

    data_json = redis_client.get(verification_key)

    if not data_json:
        logger.warning(f"Invalid or expired token: {token}")
        raise ValidationError("Invalid or expired token, please signup again")

    try:
        # Parse user data from JSON
        data = json.loads(data_json)

        # Check if user already exists
        email = data.get("email")

        new_user = create_user(data)

        # Clean up Redis keys
        _clean_verification_data(token, email)

        logger.info(f"User created and verified: {email}")
        return True

    except IntegrityError as e:
        db.session.rollback()
        logger.warning(f"User already exists with username or email.")
        raise ValidationError(
            "User with this email or username already exists. Please login instead or signup again."
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error verifying user: {str(e)}")
        raise ValidationError(f"Invalid or expired token, please signup again")


def _clean_verification_data(token, email):
    """Clean up Redis keys after verification."""
    verification_key = f"verification_token:{token}"
    signup_key = f"user_signup:{email}"

    redis_client.delete(verification_key)
    redis_client.delete(signup_key)


def is_email(login_str):
    """Check if string is an email format."""
    # Simple regex for basic email validation
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(email_regex, login_str) is not None


def authenticate_user(login_identifier, password):
    """
    Authenticate a user by username or email and password.
    """
    # Determine if the login identifier is an email or username
    if is_email(login_identifier):
        user = User.query.filter_by(email=login_identifier, is_deleted=False).first()
        identifier_type = "email"
    else:
        user = User.query.filter_by(username=login_identifier, is_deleted=False).first()
        identifier_type = "username"

    if not user:
        logger.warning(
            f"Login attempt with non-existent {identifier_type}: {login_identifier}"
        )
        raise ValidationError("Invalid username/email or password")

    if not user.is_verified:
        logger.warning(f"Login attempt with unverified account: {login_identifier}")
        raise ValidationError("Please verify your email before logging in")

    if not user.check_password(password):
        logger.warning(f"Failed login attempt for user: {login_identifier}")
        raise ValidationError("Invalid username/email or password")

    logger.info(f"User authenticated successfully: {login_identifier}")
    return user


def generate_tokens(user):
    """Generate access and refresh tokens for a user."""

    access_token = TokenHandler.generate_access_token(user, True)
    refresh_token = TokenHandler.generate_refresh_token(user)

    logger.info(f"Generated tokens for user: {user.username}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def send_password_reset_link(email, endpoint="auth.reset-password-confirm"):
    """
    Send a password reset link to user's email.
    """
    user = User.query.filter_by(email=email, is_deleted=False).first()

    # Check if a reset email was recently sent (rate limit)
    rate_limit_key = f"password_reset_link_rate_limit:{user.id}"
    if redis_client.exists(rate_limit_key):
        time_remaining = redis_client.ttl(rate_limit_key)
        minutes_remaining = int(time_remaining / 60) + 1

        logger.warning(f"Rate limit hit for password reset email to {email}")
        raise ValidationError(
            f"Please wait {minutes_remaining} minutes before requesting another reset link"
        )

    # Generate reset token
    token = TokenHandler.generate_password_reset_token()
    TokenHandler.store_reset_token(user.id, token)

    # Generate reset URL
    reset_url = url_for(endpoint, token=token, _external=True)

    send_password_reset_email.delay(email, reset_url)

    logger.info(f"Password reset email sent to: {email} with token: {token}")
    return True


def reset_password_with_token(token, new_password):
    """
    Reset a user's password using a valid reset token.
    """
    user_id = TokenHandler.verify_reset_token(token)
    if not user_id:
        logger.warning(f"Invalid or expired password reset token")
        raise ValidationError("Invalid or expired reset token")

    try:
        user = db.session.get(User, uuid.UUID(user_id))
        if not user or user.is_deleted:
            logger.warning(f"User not found for reset token: {token}")
            raise ValidationError("Invalid or expired reset token")

        # Update password
        user.set_password(new_password)
        db.session.commit()

        # Invalidate all existing tokens
        TokenHandler.invalidate_user_access_tokens(user.id)

        logger.info(f"Password reset successful for user: {user.email}")
        return user

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error resetting password: {str(e)}", exc_info=True)
        raise ValidationError("An error occurred while resetting your password")
