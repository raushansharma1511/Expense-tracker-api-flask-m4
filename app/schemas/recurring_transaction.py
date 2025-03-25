from marshmallow import fields, validates, validates_schema, ValidationError, EXCLUDE
from marshmallow.validate import Range
from sqlalchemy import or_
from flask import g
from datetime import datetime

from app.extensions import ma, db
from app.models.recurring_transaction import RecurringTransaction
from app.models.category import Category
from app.models.user import User
from app.models.wallet import Wallet
from app.utils.logger import logger
from app.utils.enums import UserRole, TransactionType, TransactionFrequency
from app.utils.constants import (
    AMOUNT_MIN_VALUE as min_val,
    AMOUNT_MAX_VALUE as max_val,
)


class RecurringTransactionSchema(ma.SQLAlchemyAutoSchema):
    """Schema for RecurringTransaction model - used for creation and reading"""

    class Meta:
        model = RecurringTransaction
        load_instance = True
        include_fk = True
        fields = (
            "id",
            "user_id",
            "wallet_id",
            "category_id",
            "category",
            "wallet",
            "amount",
            "description",
            "type",
            "frequency",
            "start_at",
            "end_at",
            "next_execution_at",
            "last_executed_at",
            "is_deleted",
            "created_at",
            "updated_at",
        )
        load_only = ("wallet_id", "category_id")
        dump_only = (
            "id",
            "next_execution_at",
            "last_executed_at",
            "is_deleted",
            "created_at",
            "updated_at",
            "category",
            "wallet",
        )
        unknown = EXCLUDE

    # Define nested fields
    category = fields.Nested("CategorySchema", only=("id", "name"), dump_only=True)
    wallet = fields.Nested("WalletSchema", only=("id", "name"), dump_only=True)

    # # Fields for serialization
    type = fields.Enum(TransactionType, by_value=True, required=True)
    frequency = fields.Enum(TransactionFrequency, by_value=True, required=True)

    # Validate fields
    amount = fields.Decimal(
        required=True,
        places=2,
        validate=Range(min=min_val, max=max_val),
        as_string=True,
    )

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
                raise ValidationError("Admin users cannot have recurring transactions")

        else:
            if str(value) != str(current_user.id):
                raise ValidationError(
                    "You can only create recurring transactions for yourself"
                )

    @validates("start_at")
    def validate_start_at(self, value):
        """Validate start_at is not in the past"""
        if value.date() < datetime.now().date():
            raise ValidationError("Start date cannot be in the past")

    @validates("end_at")
    def validate_end_at(self, value):
        """Validate end_at is after start_at if provided"""
        if (
            value
            and hasattr(self, "start_at")
            and self.start_at
            and value <= self.start_at
        ):
            raise ValidationError("End date must be after start date")

    @validates_schema
    def validate_transaction(self, data, **kwargs):
        """Additional validation for the whole transaction"""
        logger.debug("Performing whole recurring transaction validation")

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

        if "end_at" in data and data["end_at"]:
            if data["end_at"].date() <= data["start_at"].date():
                errors["end_at"] = ["End date must be after start date"]

        if errors:
            raise ValidationError(errors)

        logger.debug("Recurring transaction validation passed")


class RecurringTransactionUpdateSchema(ma.SQLAlchemyAutoSchema):
    """Schema for updating RecurringTransaction - can't update user_id"""

    class Meta:
        model = RecurringTransaction
        load_instance = True
        include_fk = True
        fields = (
            "category_id",
            "wallet_id",
            "amount",
            "description",
            "type",
            "frequency",
            "start_at",
            "end_at",
        )
        unknown = EXCLUDE

    # Fields for serialization
    type = fields.Enum(TransactionType, by_value=True, required=True)
    frequency = fields.Enum(TransactionFrequency, by_value=True, required=True)

    # Validate fields
    amount = fields.Decimal(
        required=True,
        places=2,
        validate=Range(min=min_val, max=max_val),
        as_string=True,
    )

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

    @validates("start_at")
    def validate_start_at(self, value):
        """Validate start_at is not in the past for updates"""
        if value.date() < datetime.now().date():
            raise ValidationError("Start date cannot be in the past")

    @validates_schema
    def validate_update_schema(self, data, **kwargs):
        """Schema-level validation for updates"""
        logger.debug(
            "Performing schema-level validation for recurring transaction update"
        )
        instance = self.instance

        # Check end_at vs start_at
        if "end_at" in data and data["end_at"]:
            # Determine the start_at to compare against (either from the update data or the existing instance)
            start_at = data.get("start_at", instance.start_at)
            if data["end_at"].date() <= start_at.date():
                raise ValidationError("End date must be after start date", "end_at")

        elif "start_at" in data and instance.end_at:
            # check that new start date is not after the end date
            if data["start_at"].date() >= instance.end_at.date():
                raise ValidationError("Start date must be before end date", "start_at")

        logger.debug("Recurring transaction update validation passed")


# Initialize schemas
recurring_transaction_schema = RecurringTransactionSchema()
recurring_transactions_schema = RecurringTransactionSchema(many=True)
recurring_transaction_update_schema = RecurringTransactionUpdateSchema()
