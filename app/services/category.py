from app.models.category import Category
from app.models.user import User
from app.utils.logger import logger
from app.utils.validators import is_valid_uuid
from marshmallow import ValidationError
from sqlalchemy import or_, func
from flask import g
from app.utils.enums import UserRole
from app.models.transaction import Transaction
from app.models.recurring_transaction import RecurringTransaction
from app.models.budget import Budget
from app.extensions import db


def get_user_categories(user, role, query_params={}):
    """
    Get categories for a user with optional filters
    """
    logger.info(f"Getting categories for user {user.id} with filters: {query_params}")

    # Start with base query depending on user type
    if role == UserRole.ADMIN.value:
        # Admin can see all categories
        logger.debug(f"User {user.id} is admin, retrieving all categories")
        query = Category.query

        # If specific user_id is provided and user is admin, filter by that
        if "user_id" in query_params and query_params["user_id"]:
            user_id = query_params["user_id"]

            if is_valid_uuid(user_id):
                query = query.filter(Category.user_id == user_id)
            else:
                logger.warning(f"Invalid user_id format in request: {user_id}")
                raise ValidationError(f"Invalid user_id format: {user_id}")

    elif role == UserRole.USER.value:
        # Normal users can see predefined and their own categories and get categories for a specific child
        if "child_id" in query_params and query_params["child_id"]:
            child_id = query_params["child_id"]

            if is_valid_uuid(child_id):

                child = user.get_child()
                if child and str(child.id) == str(child_id):
                    logger.debug(
                        f"User {user.id} is fetching categories for child {child_id}"
                    )
                    query = Category.query.filter(
                        Category.is_deleted == False,
                        Category.user_id == child_id,
                    )
                else:
                    logger.warning(f"User {user.id} is not parent of child {child_id}")
                    raise ValidationError(f"you are not parent of child {child_id}")
            else:
                logger.warning(f"Invalid child_id format in request: {child_id}")
                raise ValidationError(f"Invalid child_id format: {child_id}")

        else:
            logger.info(f"User {user.id} is fetching own and predefined categories")
            query = Category.query.filter(
                Category.is_deleted == False,
                or_(Category.is_predefined == True, Category.user_id == user.id),
            )
    else:
        # child users can see predefined and their own categories
        logger.debug(
            f"User {user.id} is child user, retrieving predefined and own categories"
        )
        query = Category.query.filter(
            Category.is_deleted == False,
            or_(Category.is_predefined == True, Category.user_id == user.id),
        )

    # Order by creation date for consistency
    query = query.order_by(Category.created_at)

    logger.debug("Category query built successfully")
    return query


def delete_category(category):
    """
    Delete (soft-delete) a category if it's not in use.
    """

    has_references = (
        db.session.query(
            db.session.query(Transaction)
            .filter(
                Transaction.category_id == category.id,
                Transaction.is_deleted == False,
            )
            .exists()
        ).scalar()
        or db.session.query(
            db.session.query(RecurringTransaction)
            .filter(
                RecurringTransaction.category_id == category.id,
                RecurringTransaction.is_deleted == False,
            )
            .exists()
        ).scalar()
        or db.session.query(
            db.session.query(Budget)
            .filter(
                Budget.category_id == category.id,
                Budget.is_deleted == False,
            )
            .exists()
        ).scalar()
    )

    if has_references:
        logger.warning(
            f"Attempt to delete category {category.id} with existing transactions, budgets, or recurring transactions"
        )
        raise ValidationError(
            "Cannot delete category with existing transactions, recurring transactions, or budgets."
        )

    # Soft delete the category
    category.is_deleted = True
    db.session.commit()
    return True
