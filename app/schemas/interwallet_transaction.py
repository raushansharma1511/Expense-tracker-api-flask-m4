from marshmallow import (
    fields,
    validates,
    validates_schema,
    ValidationError,
    EXCLUDE,
)
from marshmallow.validate import Range
from app.extensions import ma, db
from app.models.interwallet_transaction import InterWalletTransaction
from app.models.wallet import Wallet
from app.models.user import User
from flask import g
from app.utils.enums import UserRole
from app.utils.constants import (
    AMOUNT_MIN_VALUE as min_val,
    AMOUNT_MAX_VALUE as max_val,
)


class InterWalletTransactionSchema(ma.SQLAlchemyAutoSchema):
    """Schema for InterWalletTransaction model - used for creation and reading"""

    class Meta:
        model = InterWalletTransaction
        load_instance = True
        include_fk = True
        fields = (
            "id",
            "user_id",
            "source_wallet_id",
            "destination_wallet_id",
            "source_wallet",
            "destination_wallet",
            "amount",
            "transaction_at",
            "description",
            "is_deleted",
            "created_at",
            "updated_at",
        )
        load_only = ("source_wallet_id", "destination_wallet_id")
        dump_only = (
            "id",
            "is_deleted",
            "created_at",
            "updated_at",
        )
        unknown = EXCLUDE

    amount = fields.Decimal(
        required=True,
        places=2,
        as_string=True,
        validate=Range(min=min_val, max=max_val),
    )
    source_wallet = fields.Nested("WalletSchema", only=("id", "name"), dump_only=True)
    destination_wallet = fields.Nested(
        "WalletSchema", only=("id", "name"), dump_only=True
    )

    @validates("user_id")
    def validate_user_id(self, value):
        target_user = db.session.get(User, value)
        if not target_user or target_user.is_deleted:
            raise ValidationError("User not found")

        # Check permissions
        current_user = g.user
        current_user_role = g.role

        if current_user_role == UserRole.ADMIN.value:
            if target_user.role.value == UserRole.ADMIN.value:
                raise ValidationError("Admin users cannot have transactions")

        else:
            if str(value) != str(current_user.id):
                raise ValidationError("You can only create transactions for yourself")

    @validates_schema
    def validate_wallets(self, data, **kwargs):
        """
        Validate transaction data:
        1. Source and destination wallets exist and aren't deleted
        2. Source and destination are different wallets
        3. Both wallets belong to the user specified in user_id
        """
        errors = {}

        user_id = data.get("user_id")
        source_id = data.get("source_wallet_id")
        dest_id = data.get("destination_wallet_id")

        source_wallet = Wallet.query.filter(
            Wallet.id == source_id,
            Wallet.is_deleted == False,
            Wallet.user_id == user_id,
        ).first()
        if not source_wallet:
            errors["source_wallet_id"] = ["Source wallet not found"]

        dest_wallet = Wallet.query.filter(
            Wallet.id == dest_id, Wallet.is_deleted == False, Wallet.user_id == user_id
        ).first()
        if not dest_wallet:
            errors["destination_wallet_id"] = ["Destination wallet not found"]

        if errors:
            raise ValidationError(errors)

        if source_id == dest_id:
            raise ValidationError(
                "Source and destination wallets must be different",
                "destination_wallet_id",
            )


class InterWalletTransactionUpdateSchema(ma.SQLAlchemyAutoSchema):
    """Schema for updating InterWalletTransaction"""

    class Meta:
        model = InterWalletTransaction
        load_instance = True
        include_fk = True
        fields = (
            "source_wallet_id",
            "destination_wallet_id",
            "amount",
            "transaction_at",
            "description",
        )
        unknown = EXCLUDE

    amount = fields.Decimal(
        required=True,
        places=2,
        as_string=True,
        validate=Range(min=min_val, max=max_val),
    )

    @validates("source_wallet_id")
    def validate_source_wallet(self, value):
        """
        Validate source wallet:
        """
        wallet = Wallet.query.filter(
            Wallet.id == value,
            Wallet.is_deleted == False,
            Wallet.user_id == self.instance.user_id,
        ).first()
        if not wallet:
            raise ValidationError("Source wallet not found")

    @validates("destination_wallet_id")
    def validate_destination_wallet(self, value):
        """
        Validate destination wallet:
        """
        wallet = Wallet.query.filter(
            Wallet.id == value,
            Wallet.is_deleted == False,
            Wallet.user_id == self.instance.user_id,
        ).first()
        if not wallet:
            raise ValidationError("Destination wallet not found")

    @validates_schema
    def validate_wallets(self, data, **kwargs):
        """
        Cross-field validations:
        - Source and destination wallets are different
        """
        # Check if we're updating either wallet field
        if not ("source_wallet_id" in data or "destination_wallet_id" in data):
            return  # Skip validation if not updating wallets

        # Get wallet IDs (either from data or from instance)
        instance = self.instance
        source_id = data.get("source_wallet_id", instance.source_wallet_id)
        dest_id = data.get("destination_wallet_id", instance.destination_wallet_id)

        if source_id == dest_id:
            raise ValidationError(
                {
                    "destination_wallet_id": [
                        "Source and destination wallets must be different"
                    ]
                }
            )


# Initialize schemas
interwallet_transaction_schema = InterWalletTransactionSchema()
interwallet_transactions_schema = InterWalletTransactionSchema(many=True)
interwallet_transaction_update_schema = InterWalletTransactionUpdateSchema()
