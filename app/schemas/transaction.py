from marshmallow import (
    fields,
    validates,
    ValidationError,
    validates_schema,
    EXCLUDE,
)
from sqlalchemy import or_
from marshmallow.validate import Range
from flask import g

from app.extensions import ma, db
from app.models.transaction import Transaction, TransactionType
from app.models.category import Category
from app.models.user import User
from app.models.wallet import Wallet
from app.utils.logger import logger
from app.utils.enums import UserRole
from app.utils.constants import (
    AMOUNT_MIN_VALUE as min_val,
    AMOUNT_MAX_VALUE as max_val,
)


class TransactionSchema(ma.SQLAlchemyAutoSchema):
    """Schema for Transaction model - used for creation and reading"""

    class Meta:
        model = Transaction
        load_instance = True
        include_fk = True
        fields = (
            "id",
            "user_id",
            "type",
            "category_id",
            "wallet_id",
            "category",
            "wallet",
            "amount",
            "transaction_at",
            "description",
            "is_deleted",
            "created_at",
            "updated_at",
        )
        dump_only = ("id", "is_deleted", "created_at", "updated_at")
        load_only = ("category_id", "wallet_id")
        unknown = EXCLUDE

    type = fields.Enum(TransactionType, by_value=True, required=True)
    amount = fields.Decimal(
        required=True,
        places=2,
        validate=Range(min=min_val, max=max_val),
        as_string=True,
    )
    category = fields.Nested("CategorySchema", only=("id", "name"), dump_only=True)
    wallet = fields.Nested("WalletSchema", only=("id", "name"), dump_only=True)

    @validates("user_id")
    def validate_user_id(self, value):
        """Validate user_id field"""
        logger.debug(f"Validating user_id: {value}")
        # Check if the user exists
        target_user = db.session.get(User, value)

        if not target_user or target_user.is_deleted:
            raise ValidationError("User not found")

        current_user = g.user
        current_user_role = g.role

        if current_user_role == UserRole.ADMIN.value:
            if target_user.role.value == UserRole.ADMIN.value:
                raise ValidationError("Admin users cannot have transactions")

        else:
            if str(value) != str(current_user.id):
                raise ValidationError("You can only create transactions for yourself")

    @validates_schema
    def validate_transaction(self, data, **kwargs):
        """Additional validation for the whole transaction"""
        logger.debug("Performing whole transaction validation")

        user_id = data["user_id"]
        category_id = data["category_id"]
        wallet_id = data["wallet_id"]

        errors = {}

        category = Category.query.filter(
            Category.id == category_id,
            Category.is_deleted == False,
            or_(Category.is_predefined == True, Category.user_id == user_id),
        ).first()
        if not category:
            errors["category_id"] = ["Category not found"]

        wallet = Wallet.query.filter(
            Wallet.id == wallet_id,
            Wallet.is_deleted == False,
            Wallet.user_id == user_id,
        ).first()
        if not wallet:
            errors["wallet_id"] = ["Wallet not found"]

        if errors:
            raise ValidationError(errors)

        logger.debug("Transaction validation passed")


class TransactionUpdateSchema(ma.SQLAlchemyAutoSchema):
    """Schema for updating Transaction - can't update user_id or type"""

    class Meta:
        model = Transaction
        load_instance = True
        include_fk = True
        fields = (
            "category_id",
            "wallet_id",
            "amount",
            "type",
            "transaction_at",
            "description",
        )
        unknown = EXCLUDE

    amount = fields.Decimal(
        required=True,
        places=2,
        validate=Range(min=min_val, max=max_val),
        as_string=True,
    )
    type = fields.Enum(TransactionType, by_value=True, required=True)

    @validates("category_id")
    def validate_category_id(self, value):
        """Validate category_id field"""
        logger.debug(f"Validating category_id for update: {value}")

        category = Category.query.filter(
            Category.id == value,
            Category.is_deleted == False,
            or_(
                Category.is_predefined == True,
                Category.user_id == self.instance.user_id,
            ),
        ).first()
        if not category:
            raise ValidationError("Category not found")

        logger.debug(f"Update category_id validation passed for ID {value}")
        return value

    @validates("wallet_id")
    def validate_wallet_id(self, value):
        """Validate wallet for update"""
        logger.debug(f"Validating wallet_id for update: {value}")

        wallet = Wallet.query.filter(
            Wallet.id == value,
            Wallet.is_deleted == False,
            Wallet.user_id == self.instance.user_id,
        ).first()
        if not wallet:
            raise ValidationError("Wallet not found")

        logger.debug(f"Update wallet_id validation passed for ID {value}")
        return value


# Initialize schemas
transaction_schema = TransactionSchema()
transactions_schema = TransactionSchema(many=True)
transaction_update_schema = TransactionUpdateSchema()
