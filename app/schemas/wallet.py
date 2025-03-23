from marshmallow import fields, validates, ValidationError, EXCLUDE, validates_schema
from marshmallow.validate import Length
from app.extensions import ma, db
from app.models.wallet import Wallet
from app.models.user import User
from app.utils.validators import normalize_name
from app.utils.enums import UserRole
from app.utils.constants import (
    WALLET_NAME_MIN_LENGTH as min_len,
    WALLET_NAME_MAX_LENGTH as max_len,
)
from flask import g


class WalletSchema(ma.SQLAlchemyAutoSchema):
    """Schema for Wallet model - used for creation and reading"""

    class Meta:
        model = Wallet
        load_instance = True
        include_fk = True
        fields = (
            "id",
            "name",
            "balance",
            "user_id",
            "is_deleted",
            "created_at",
            "updated_at",
        )
        dump_only = ("id", "balance", "is_deleted", "created_at", "updated_at")
        unknown = EXCLUDE

    name = fields.String(required=True, validate=Length(min=min_len, max=max_len))
    balance = fields.Decimal(places=2, as_string=True, dump_only=True)

    @validates("user_id")
    def validate_user_id(self, value):
        """
        Validate user_id based on role permissions

        Rules:
        - ADMIN can create wallets for any non-admin user
        - USER can only create wallets for themselves
        - CHILD_USER can only create wallets for themselves
        """
        target_user = db.session.get(User, value)
        if not target_user or target_user.is_deleted:
            raise ValidationError("User not found")

        # Get current user and role
        current_user = g.user
        current_user_role = g.role

        if current_user_role == UserRole.ADMIN.value:
            if target_user.role.value == UserRole.ADMIN.value:
                raise ValidationError("Admin users cannot have wallets")

        else:
            if str(value) != str(current_user.id):
                raise ValidationError("You can only create wallets for yourself")

    @validates_schema
    def validate_name_uniqueness(self, data, **kwargs):
        """
        Validate wallet name uniqueness for a user.
        """
        name = data["name"]
        normalized_name = normalize_name(name)

        if not normalized_name:
            raise ValidationError(
                {
                    "name": [
                        "Wallet name is not valid, it must include at least one character"
                    ]
                }
            )
        user_id = data["user_id"]

        exists = (
            db.session.query(Wallet)
            .filter(
                Wallet.is_deleted == False,
                Wallet.name == normalized_name,
                Wallet.user_id == user_id,
            )
            .first()
            is not None
        )
        if exists:
            raise ValidationError({"name": ["A wallet with this name already exists"]})

        data["name"] = normalized_name


class WalletUpdateSchema(ma.SQLAlchemyAutoSchema):
    """Schema for updating Wallet - only name can be updated"""

    class Meta:
        model = Wallet
        load_instance = True
        fields = ("name",)
        unknown = EXCLUDE

    name = fields.String(required=True, validate=Length(min=min_len, max=max_len))

    @validates("name")
    def validate_name(self, value):
        """Validate name and ensure it's unique for this user"""
        normalized_name = normalize_name(value)

        if not normalized_name:
            raise ValidationError("Wallet name cannot be empty")

        # Get the current instance being updated
        instance = self.instance

        # Skip validation if normalized name is unchanged
        if instance.name == normalized_name:
            return normalized_name

        # Check if a wallet with this name already exists for this user
        exists = (
            db.session.query(Wallet)
            .filter(
                Wallet.is_deleted == False,
                Wallet.id != instance.id,
                Wallet.name == normalized_name,
                Wallet.user_id == instance.user_id,
            )
            .first()
            is not None
        )
        if exists:
            raise ValidationError("A wallet with this name already exists")

        return normalized_name


# Initialize schemas
wallet_schema = WalletSchema()
wallets_schema = WalletSchema(many=True)
wallet_update_schema = WalletUpdateSchema()
