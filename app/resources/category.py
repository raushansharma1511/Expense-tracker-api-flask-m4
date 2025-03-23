from flask_restful import Resource
from flask import request, g
from marshmallow import ValidationError
from sqlalchemy import or_

from app.extensions import db
from app.models.category import Category
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.category import (
    category_schema,
    categories_schema,
    category_update_schema,
)
from app.services.category import get_user_categories, delete_category
from app.utils.permissions import (
    authenticated_user,
    object_permission,
    category_permission,
)
from app.utils.responses import validation_error_response
from app.utils.pagination import paginate
from app.utils.validators import normalize_name
from app.utils.logger import logger


class CategoryListResource(Resource):
    """Resource for listing and creating categories"""

    method_decorators = [authenticated_user]

    def get(self):
        """Get paginated list of categories"""
        # Get query parameters
        user = g.user
        user_role = g.role
        query_params = request.args.to_dict()

        query = get_user_categories(user, user_role, query_params)

        # Use pagination utility
        result = paginate(
            query=query, schema=categories_schema, endpoint="category.categories"
        )
        logger.info(f"category retrieved succesfully by user {user}")
        return result, 200

    def post(self):
        """Create a new category"""
        try:
            # Get data
            data = request.get_json() or {}
            logger.info(
                f"Category creation request received by user {g.user.id}: {data}"
            )

            # Validate and create category
            category = category_schema.load(data)

            # Save to database
            db.session.add(category)
            db.session.commit()
            logger.info(
                f"Category created successfully: {category.id} by user {g.user.id}"
            )

            return category_schema.dump(category), 201

        except ValidationError as err:
            return validation_error_response(err)


class CategoryDetailResource(Resource):
    """Resource for retrieving, updating and deleting a category"""

    method_decorators = [
        object_permission(Category, check_fn=category_permission),
        authenticated_user,
    ]

    def get(self, id):
        """Get a specific category"""
        # Object is already loaded by permission decorator
        category = g.object
        logger.info(
            f"Category {category.id} retrieved successfully by user {g.user.id}"
        )
        return category_schema.dump(category), 200

    def patch(self, id):
        """Update a specific category's name"""
        try:
            category = g.object  # Object is already loaded by permission decorator
            data = request.get_json() or {}

            logger.info(
                f"Category update request for {category.id} by user {g.user.id}: {data}"
            )

            updated_category = category_update_schema.load(
                data, instance=category, partial=True
            )
            updated_category.name = normalize_name(updated_category.name)
            db.session.commit()

            logger.info(
                f"Category updated successfully: {updated_category.id} by user {g.user.id}"
            )
            return category_schema.dump(updated_category), 200

        except ValidationError as err:
            return validation_error_response(err)

    def delete(self, id):
        """Delete a specific category"""
        # Object is already loaded by permission decorator
        try:
            category = g.object

            logger.info(
                f"Category deletion request for {category.id} by user {g.user.id}"
            )
            delete_category(category)

            logger.info(
                f"Category soft deleted successfully: {category.id} by user {g.user.id}"
            )
            return "", 204
        except ValidationError as err:
            return validation_error_response(err)
