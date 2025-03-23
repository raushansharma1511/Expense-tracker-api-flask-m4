from datetime import datetime
from decimal import Decimal
from marshmallow import ValidationError
from sqlalchemy import extract

from app.utils.validators import is_valid_uuid
from app.models.transaction import Transaction
from app.tasks.budget import check_budget_thresholds
from app.models.budget import Budget
from app.utils.logger import logger
from app.extensions import db
from app.services.common import fetch_standard_resources
from app.utils.enums import TransactionType


def get_user_budgets(user, role, query_params=None):
    """
    Get budgets based on user role and query parameters.

    Args:
        user: The user requesting budgets
        role: The role of the requesting user
        query_params: Dict with optional filters:
            - user_id: For ADMIN to filter by specific user
            - child_id: For USER to filter by their child
            - category_id: Filter by specific category
            - month: Filter by month (1-12)
            - year: Filter by year
    """
    if query_params is None:
        query_params = {}

    # Get base query with standard role-based filtering
    query = fetch_standard_resources(
        model_class=Budget,
        user=user,
        role=role,
        query_params=query_params,
    )

    # Apply additional filters
    if "category_id" in query_params and query_params["category_id"]:
        category_id = query_params["category_id"]

        if is_valid_uuid(category_id):
            query = query.filter(Budget.category_id == category_id)
        else:
            raise ValidationError(f"Invalid category_id format {category_id}")

    if "month" in query_params and query_params["month"]:
        if "year" not in query_params or not query_params["year"]:
            raise ValidationError(
                "Filtering by month requires specifying a year as well."
            )

        try:
            month = int(query_params["month"])
            year = int(query_params["year"])

            if not (1 <= month <= 12):
                raise ValidationError("Month must be between 1 and 12")

            query = query.filter(Budget.month == month, Budget.year == year)
        except (ValueError, TypeError):
            logger.warning(f"Invalid month/year parameters: {query_params}")
            raise ValidationError("Invalid month or year format.")

    elif "year" in query_params and query_params["year"]:
        try:
            year = int(query_params["year"])

            query = query.filter(Budget.year == year)
        except (ValueError, TypeError):
            logger.warning(f"Invalid year parameter: {query_params['year']}")
            raise ValidationError("Invalid year format.")

    # Apply default ordering (by year desc, month desc)
    query = query.order_by(Budget.year.desc(), Budget.month.desc())

    return query


def create_budget(budget):
    """
    Create a new budget with initial spent amount calculation
    """
    try:
        # Calculate existing spending for this month/year/category
        spent_amount = calculate_month_spending(
            budget.user_id, budget.category_id, budget.month, budget.year
        )

        # Set the calculated spent amount
        budget.spent_amount = spent_amount

        db.session.add(budget)
        db.session.commit()

        logger.info(
            f"Created budget {budget.id} for {budget.user_id}, {budget.category_id}, {budget.month}/{budget.year} with initial spent_amount {spent_amount}"
        )

        # Queue Celery task to check if budget already exceeding thresholds
        check_budget_thresholds.delay(budget.id)

        return budget

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating budget: {str(e)}")
        return {"error": f"Failed to create budget: {str(e)}"}, 500


def update_budget(updated_budget, old_budget):
    """Update a budget amount"""
    try:
        old_amount = old_budget.amount
        old_category_id = old_budget.category_id

        new_amount = updated_budget.amount
        new_category_id = updated_budget.category_id

        amount_changed = old_amount != new_amount
        category_changed = str(old_category_id) != str(new_category_id)

        if category_changed:
            new_spent_amount = calculate_month_spending(
                updated_budget.user_id,
                updated_budget.category_id,
                updated_budget.month,
                updated_budget.year,
            )
            updated_budget.spent_amount = new_spent_amount
            updated_budget.exceeded_notification_sent = False
            updated_budget.warning_notification_sent = False
            logger.info(
                f"Updated budget {updated_budget.id} category from {old_category_id} to {new_category_id} "
                f"with new spent_amount {new_spent_amount}"
            )

        if amount_changed:
            logger.info(
                f"Updated budget {updated_budget.id} amount from {old_amount} to {new_amount}"
            )
        db.session.commit()
        if amount_changed or category_changed:
            check_budget_thresholds.delay(updated_budget.id)
        return updated_budget

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating budget: {str(e)}")
        return {"error": f"Failed to update budget: {str(e)}"}, 500


def calculate_month_spending(user_id, category_id, month, year):
    """
    Calculate total spending for a specific month/year/category

    Args:
        user_id: User ID
        category_id: Category ID
        month: Month (1-12)
        year: Year

    Returns:
        Decimal: Total spending amount
    """
    # Query for transactions in the given month/year for this category and user
    transactions = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.category_id == category_id,
        extract("month", Transaction.transaction_at) == month,
        extract("year", Transaction.transaction_at) == year,
        Transaction.is_deleted == False,
        Transaction.type == TransactionType.DEBIT,  # Only count expense transactions
    ).all()

    # Sum up the amounts
    total = Decimal("0.00")
    for transaction in transactions:
        total += transaction.amount

    return total
