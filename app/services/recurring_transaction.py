from app.models.recurring_transaction import RecurringTransaction
from app.models.wallet import Wallet
from app.utils.logger import logger
from app.extensions import db
from app.services.common import fetch_standard_resources
from sqlalchemy import or_
from datetime import datetime, timedelta
from marshmallow import ValidationError
from app.utils.validators import is_valid_uuid
import calendar
from dateutil.relativedelta import relativedelta
from app.utils.enums import TransactionType, TransactionFrequency


def get_user_recurring_transactions(user, role, query_params=None):
    """
    Get recurring transactions based on user role and query parameters.

    Args:
        user: The user requesting recurring transactions
        role: The role of the requesting user
        query_params: Dict with optional filters:
            - user_id: For ADMIN to filter by specific user
            - child_id: For USER to filter by their child
            - wallet_id: Filter by specific wallet
            - category_id: Filter by specific category
            - type: Filter by transaction type (credit/debit)
            - frequency: Filter by frequency
    """
    if query_params is None:
        query_params = {}

    # Get base query with standard role-based filtering
    query = fetch_standard_resources(
        model_class=RecurringTransaction,
        user=user,
        role=role,
        query_params=query_params,
    )

    # Apply additional filters
    if "wallet_id" in query_params and query_params["wallet_id"]:
        wallet_id = query_params["wallet_id"]

        if is_valid_uuid(wallet_id):
            query = query.filter(RecurringTransaction.wallet_id == wallet_id)
        else:
            raise ValidationError(f"Invalid wallet_id format {wallet_id}")

    if "category_id" in query_params and query_params["category_id"]:
        category_id = query_params["category_id"]

        if is_valid_uuid(category_id):
            query = query.filter(RecurringTransaction.category_id == category_id)
        else:
            raise ValidationError(f"Invalid category_id format {category_id}")

    if "type" in query_params and query_params["type"]:
        try:
            transaction_type = TransactionType(query_params["type"])
            query = query.filter(RecurringTransaction.type == transaction_type)
        except ValueError:
            raise ValidationError(f"Invalid transaction type: {query_params['type']}")

    if "frequency" in query_params and query_params["frequency"]:
        try:
            frequency = TransactionFrequency(query_params["frequency"])
            query = query.filter(RecurringTransaction.frequency == frequency)
        except ValueError:
            raise ValidationError(f"Invalid frequency: {query_params['frequency']}")

    # Order by next execution date
    query = query.order_by(RecurringTransaction.next_execution_at)

    logger.debug("Recurring Transaction query built successfully")
    return query


def create_recurring_transaction(recurring_transaction):
    """
    Create a new recurring transaction.

    Args:
        recurring_transaction: RecurringTransaction object

    Returns:
        The created RecurringTransaction or error tuple
    """
    try:
        # Set next execution date to start_at
        recurring_transaction.next_execution_at = recurring_transaction.start_at

        # Add to database
        db.session.add(recurring_transaction)
        db.session.commit()

        logger.info(f"Created recurring transaction: {recurring_transaction.id}")
        return recurring_transaction

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating recurring transaction: {str(e)}")
        return {"error": f"Failed to create recurring transaction: {str(e)}"}, 500


def update_recurring_transaction(recurring_transaction, update_data):
    """
    Update an existing recurring transaction.

    Args:
        recurring_transaction: The RecurringTransaction to update
        update_data: Dict with fields to update

    Returns:
        Updated RecurringTransaction or error tuple
    """
    try:
        # Check if start_at is being updated
        start_at_updated = "start_at" in update_data

        # If start_at was updated, set next_execution_at to the new start_at
        if start_at_updated:
            recurring_transaction.next_execution_at = recurring_transaction.start_at

        # Save changes
        db.session.commit()

        logger.info(f"Updated recurring transaction: {recurring_transaction.id}")
        return recurring_transaction

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating recurring transaction: {str(e)}")
        return {"error": f"Failed to update recurring transaction: {str(e)}"}, 500


def calculate_next_execution_date(recurring_transaction, from_date=None):
    """
    Calculate the next execution date for a recurring transaction.

    Args:
        recurring_transaction: RecurringTransaction object
        from_date: Date to calculate from (defaults to current next_execution_at or now)
    Returns:
        datetime: Next execution date
    """
    # Use the provided date, or current next_execution_at, or current date
    base_date = from_date
    if base_date is None:
        base_date = recurring_transaction.next_execution_at or datetime.now()

    frequency = recurring_transaction.frequency

    if frequency == TransactionFrequency.DAILY:
        next_date = base_date + timedelta(days=1)

    elif frequency == TransactionFrequency.WEEKLY:
        next_date = base_date + timedelta(weeks=1)

    elif frequency == TransactionFrequency.MONTHLY:
        # Get the day from the start date
        target_day = recurring_transaction.start_at.day

        # Calculate next month's date
        next_month = base_date + relativedelta(months=1)

        # Check if the target day exists in the next month
        last_day_of_month = calendar.monthrange(next_month.year, next_month.month)[1]
        day = min(target_day, last_day_of_month)

        # Create the next date
        next_date = next_month.replace(day=day)

    elif frequency == TransactionFrequency.YEARLY:
        next_date = calculate_next_yearly_date(recurring_transaction, base_date)

    # Preserve the original time
    if recurring_transaction.start_at:
        next_date = next_date.replace(
            hour=recurring_transaction.start_at.hour,
            minute=recurring_transaction.start_at.minute,
            second=recurring_transaction.start_at.second,
        )

    return next_date


def calculate_next_yearly_date(recurring_transaction, base_date):
    """
    Calculate next yearly execution date, properly handling leap years.
    """
    next_year = base_date.year + 1
    original_month = recurring_transaction.start_at.month
    original_day = recurring_transaction.start_at.day

    # Adjust day for month-end or leap year
    if original_month == 2 and original_day == 29:
        adjusted_day = 29 if calendar.isleap(next_year) else 28
    else:
        adjusted_day = min(
            original_day, calendar.monthrange(next_year, original_month)[1]
        )

    return datetime(year=next_year, month=original_month, day=adjusted_day)
