from marshmallow import (
    fields,
    validates,
    ValidationError,
    EXCLUDE,
    validates_schema,
)
from marshmallow.validate import Length
from app.extensions import ma, db
from app.models.category import Category
from app.models.user import User
from app.utils.validators import normalize_name
from app.utils.constants import (
    CATEGORY_NAME_MIN_LENGTH as min_len,
    CATEGORY_NAME_MAX_LENGTH as max_len,
)
from flask import g
from sqlalchemy import or_, func
from app.utils.enums import UserRole


class CategorySchema(ma.SQLAlchemyAutoSchema):
    """Schema for Category model - used for creation and reading"""

    class Meta:
        model = Category
        load_instance = True
        include_fk = True
        fields = (
            "id",
            "name",
            "user_id",
            "is_predefined",
            "is_deleted",
            "created_at",
            "updated_at",
        )
        dump_only = ("id", "is_predefined", "is_deleted", "created_at", "updated_at")
        unknown = EXCLUDE

    # UUID field handles format validation automatically
    name = fields.String(required=True, validate=Length(min=min_len, max=max_len))

    @validates("user_id")
    def validate_user_id(self, value):
        """Validate user_id - this runs after format validation"""
        # Check if the user exists
        user = db.session.get(User, value)
        if not user or user.is_deleted:
            raise ValidationError("User not found")

        # Get current user for permission check
        current_user = g.user
        current_user_role = g.role

        if current_user_role == UserRole.ADMIN.value:
            return value
        else:
            if str(value) != str(current_user.id):
                raise ValidationError("You can create categories for yourself only")

        return value

    @validates_schema
    def validate_name_uniqueness(self, data, **kwargs):
        """
        Validate name uniqueness using the validated user_id.
        This runs after all field-level validators.
        """
        # Normalize the name
        name = data["name"]
        normalized_name = normalize_name(name)

        # If normalized name is empty, raise error
        if not normalized_name:
            raise ValidationError(
                {
                    "name": [
                        "Category name is not valid, it must include characters and digits"
                    ]
                }
            )

        # Use the validated user_id which we know is valid at this point
        user_id = data["user_id"]
        user = db.session.get(User, user_id)

        # Check if a category with this normalized name already exists for this user or as a predefined category
        # Using func.lower for case-insensitive comparison
        exists = (
            db.session.query(Category)
            .filter(
                Category.is_deleted == False,
                Category.name == normalized_name,
            )
            .filter((Category.user_id == user_id) | (Category.is_predefined == True))
            .first()
            is not None
        )

        if exists:
            raise ValidationError(
                {"name": ["A category with this name already exists"]}
            )

        # Store normalized name back in data
        data["name"] = normalized_name
        data["is_predefined"] = user.is_admin


class CategoryUpdateSchema(ma.SQLAlchemyAutoSchema):
    """Schema for updating Category - only name can be updated"""

    class Meta:
        model = Category
        load_instance = True
        fields = ("name",)
        unknown = EXCLUDE

    name = fields.String(required=True, validate=Length(min=min_len, max=max_len))

    @validates("name")
    def validate_name(self, value):
        """Validate name and ensure it's unique for this user"""
        # Normalize the name here directly
        normalized_name = normalize_name(value)

        if not normalized_name:
            raise ValidationError(
                "Category name is not valid, it must include characters and digits"
            )

        # Get the current instance being updated
        instance = self.instance

        # Skip validation if normalized name is unchanged
        if instance.name == normalized_name:
            return normalized_name

        # Check if a category with this normalized name already exists for this user or as a predefined category
        exists = (
            db.session.query(Category)
            .filter(
                Category.is_deleted == False,
                Category.id != instance.id,
                Category.name == normalized_name,
            )
            .filter(
                (Category.user_id == instance.user_id)
                | (Category.is_predefined == True)
            )
            .first()
            is not None
        )
        if exists:
            raise ValidationError("A category with this name already exists")


# Initialize schemas
category_schema = CategorySchema()
categories_schema = CategorySchema(many=True)
category_update_schema = CategoryUpdateSchema()
