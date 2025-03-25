from marshmallow import validate, ValidationError
import re
import uuid

from app.models.user import User
from app.extensions import db
from app.utils.logger import logger


def validate_username(value):
    """Ensure username only contains letters, numbers, and underscores."""
    if not re.match(r"^[a-zA-Z0-9_]+$", value):
        raise ValidationError(
            "Username must contain only letters, numbers, underscores, dots, or hyphens."
        )

    existing_user = db.session.query(User).filter_by(username=value).first()
    if existing_user:
        raise ValidationError("Username is already taken.")


def validate_email(value):
    """Ensure email is unique."""
    existing_email = db.session.query(User).filter_by(email=value).first()
    if existing_email:
        raise ValidationError("Email is already in use.")


def validate_password(value):
    """
    Validates the password with the following conditions:
    - Must be at least 8 characters long.
    - Must contain at least one letter.
    - Must contain at least one digit.
    - Must contain at least one special character.
    """
    min_length = 8
    special_char_pattern = r'[!@#$%^&*(),.?":{}|<>]'
    digit_pattern = r"\d"
    letter_pattern = r"[a-zA-Z]"

    if value != value.strip():
        raise ValidationError(
            "Password must not contain leading or trailing whitespace."
        )

    # Check if password length is at least 8 characters
    if len(value) < min_length:
        raise ValidationError("Password must be at least 8 characters long.")

    # Check if password contains at least one letter
    if not re.search(letter_pattern, value):
        raise ValidationError("Password must contain at least one letter.")

    # Check if password contains at least one digit
    if not re.search(digit_pattern, value):
        raise ValidationError("Password must contain at least one digit.")

    # Check if password contains at least one special character
    if not re.search(special_char_pattern, value):
        raise ValidationError("Password must contain at least one special character.")

    return value


def is_valid_uuid(value):
    try:
        uuid_obj = uuid.UUID(value)
        return True
    except ValueError as e:
        return False


def normalize_name(name):
    """
    Normalize a name by removing extra spaces, special characters,
    and standardizing the format.
    """
    if not name:
        return ""

    # Convert to lowercase and trim whitespace
    normalized = name.lower().strip()

    # Replace multiple spaces, dashes, or special chars with a single space
    normalized = re.sub(r"[\s\-_]+", " ", normalized)

    # Remove any remaining non-alphanumeric chars (except spaces)
    normalized = re.sub(r"[^\w\s]", "", normalized)

    normalized = normalized.capitalize().strip()
    return normalized
