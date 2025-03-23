from datetime import date
from marshmallow import (
    fields,
    validate,
    validates,
    ValidationError,
    EXCLUDE,
    validates_schema,
)
from app.extensions import ma
from app.models.user import User
from app.utils.validators import validate_email, validate_password, validate_username
from app.utils.enums import Gender


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        fields = [
            "id",
            "username",
            "email",
            "password",
            "name",
            "date_of_birth",
            "gender",
            "role",
            "is_verified",
            "is_deleted",
            "created_at",
            "updated_at",
        ]

        load_only = ["password"]
        dump_only = [
            "id",
            "is_deleted",
            "created_at",
            "updated_at",
            "role",
            "is_verified",
        ]
        unknown = EXCLUDE

    username = fields.String(
        required=True, validate=[validate.Length(min=5, max=120), validate_username]
    )
    email = fields.Email(required=True, validate=validate_email)
    password = fields.String(required=True, validate=validate_password, load_only=True)
    gender = fields.Enum(Gender, by_value=True)

    @validates("date_of_birth")
    def validate_date_of_birth(self, value):
        """Ensure date of birth is not in the future and is after the year 1900."""
        if value >= date.today():
            raise ValidationError("Date of birth cannot be in the future.")

        if value.year < 1880:
            raise ValidationError("Date of birth must be after the year 1880.")

        return value


class LoginSchema(ma.Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)


class PasswordResetRequestSchema(ma.Schema):
    email = fields.Email(required=True, validate=validate.Length(max=120))

    @validates("email")
    def validate_email(self, value):
        user = User.query.filter_by(
            email=value, is_deleted=False, is_verified=True
        ).first()
        if not user:
            raise ValidationError("No user found with this email address.")
        return value


class PasswordResetConfirmSchema(ma.Schema):
    password = fields.String(required=True, validate=validate_password)
    confirm_password = fields.String(required=True)

    @validates_schema
    def validate_passwords(self, data, **kwargs):
        if data.get("password") != data.get("confirm_password"):
            raise ValidationError("Passwords must match", "confirm_password")


user_schema = UserSchema()
login_schema = LoginSchema()
password_reset_request_schema = PasswordResetRequestSchema()
password_reset_confirm_schema = PasswordResetConfirmSchema()
