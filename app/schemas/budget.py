from marshmallow import fields, validates, validates_schema, ValidationError, EXCLUDE
from marshmallow.validate import Range
from sqlalchemy import or_
from app.extensions import ma, db
from app.models.budget import Budget
from app.models.category import Category
from app.models.user import User
from app.utils.enums import UserRole
from app.utils.constants import AMOUNT_MIN_VALUE, AMOUNT_MAX_VALUE
from flask import g
from decimal import Decimal
import datetime
from app.utils.logger import logger


class BudgetSchema(ma.SQLAlchemyAutoSchema):
    """Schema for Budget model - used for creation and reading"""

    class Meta:
        model = Budget
        load_instance = True
        include_fk = True
        fields = (
            "id",
            "user_id",
            "category_id",
            "category",
            "amount",
            "spent_amount",
            "month",
            "year",
            "is_deleted",
            "created_at",
            "updated_at",
        )
        dump_only = (
            "id",
            "spent_amount",
            "is_deleted",
            "created_at",
            "updated_at",
        )
        load_only = ("category_id",)
        unknown = EXCLUDE

    # Validation for fields
    amount = fields.Decimal(
        required=True,
        places=2,
        as_string=True,
        validate=Range(min=AMOUNT_MIN_VALUE, max=AMOUNT_MAX_VALUE),
    )
    spent_amount = fields.Decimal(places=2, as_string=True, dump_only=True)
    category = fields.Nested("CategorySchema", only=("id", "name"), dump_only=True)

    @validates("user_id")
    def validate_user_id(self, value):
        """
        Validate that:
        1. The user exists and is not deleted
        2. The current user has permission to create budgets for this user
        """
        target_user = db.session.get(User, value)
        if not target_user or target_user.is_deleted:
            raise ValidationError("User not found")

        # Check permissions
        current_user = g.user
        current_user_role = g.role

        if current_user_role == UserRole.ADMIN.value:
            if target_user.role.value == UserRole.ADMIN.value:
                raise ValidationError("Admin users cannot have budgets")
            return value

        else:
            if str(value) != str(current_user.id):
                raise ValidationError("You can only create budgets for yourself")
            return value

    @validates("month")
    def validate_month(self, value):
        """Validate month is between 1-12"""
        if not 1 <= value <= 12:
            raise ValidationError("Month must be between 1 and 12")
        return value

    @validates("year")
    def validate_year(self, value):
        """Validate year is reasonable (not too far in past or future)"""
        current_year = datetime.datetime.now().year
        if not (current_year) <= value <= (current_year + 5):
            raise ValidationError(
                f"Year must be between {current_year} and {current_year+5}"
            )
        return value

    @validates_schema
    def validate_unique_budget(self, data, **kwargs):
        """
        Validate uniqueness: one budget per user-category-month-year
        """

        user_id = data["user_id"]
        category_id = data["category_id"]
        month = data["month"]
        year = data["year"]

        category = Category.query.filter(
            Category.id == category_id,
            Category.is_deleted == False,
            or_(Category.is_predefined == True, Category.user_id == user_id),
        ).first()

        if not category:
            raise ValidationError("Category not found", "category_id")

        current_month = datetime.datetime.now().month
        if month < current_month and year == datetime.datetime.now().year:
            raise ValidationError("Cannot create budget for past months", "month")

        # Query for existing budget
        existing = Budget.query.filter(
            Budget.user_id == user_id,
            Budget.category_id == category_id,
            Budget.month == month,
            Budget.year == year,
            Budget.is_deleted == False,
        ).first()

        if existing:
            raise ValidationError(
                "A budget already exists for this user, category, month and year",
                "month_year",
            )


class BudgetUpdateSchema(ma.SQLAlchemyAutoSchema):
    """Schema for updating Budget - only amount can be changed"""

    class Meta:
        model = Budget
        load_instance = True
        include_fk = True
        fields = ("amount", "category_id")
        unknown = EXCLUDE

    amount = fields.Decimal(
        required=False,
        places=2,
        as_string=True,
        validate=Range(min=AMOUNT_MIN_VALUE, max=AMOUNT_MAX_VALUE),
    )

    @validates("category_id")
    def validate_category_id(self, value):
        """Validate category exists and is not deleted"""
        logger.debug(f"Validating category_id: {value}")

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

        existing = Budget.query.filter(
            Budget.user_id == self.instance.user_id,
            Budget.category_id == value,
            Budget.category_id != self.instance.category_id,
            Budget.month == self.instance.month,
            Budget.year == self.instance.year,
            Budget.is_deleted == False,
        ).first()

        if existing:
            raise ValidationError(
                "A budget already exists for this user, category, month and year",
                "month_year",
            )

        logger.debug("Category validation passed")
        return value


# Create schema instances
budget_schema = BudgetSchema()
budgets_schema = BudgetSchema(many=True)
budget_update_schema = BudgetUpdateSchema()
