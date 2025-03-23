from sqlalchemy import func, case
from datetime import datetime, timezone
from marshmallow import ValidationError

from app.models.transaction import Transaction, TransactionType
from app.models.category import Category
from app.models.wallet import Wallet
from app.utils.logger import logger
from app.services.common import fetch_standard_resources
from app.models.interwallet_transaction import InterWalletTransaction
from app.utils.enums import UserRole


def parse_and_validate_dates(start_date, end_date):
    """
    Parse and validate start_date and end_date
    """
    if not start_date or not end_date:
        raise ValidationError("Both start_date and end_date are required")

    try:
        # Parse dates and ensure they are at the start/end of the day
        parsed_start = datetime.strptime(start_date, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
        parsed_end = datetime.strptime(end_date, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc
        )
        if parsed_start > parsed_end:
            raise ValidationError("Start date cannot be after end date")

        return parsed_start, parsed_end
    except ValueError:
        raise ValidationError("Invalid start or end date format. Use YYYY-MM-DD")


def get_transactions_query(user, role, start_date, end_date, query_params={}):
    """
    Get transaction query filtered by date range and user permissions
    """
    query = fetch_standard_resources(
        model_class=Transaction,
        user=user,
        role=role,
        query_params=query_params,
    )
    # Filter by date range
    query = query.filter(
        Transaction.transaction_at >= start_date,
        Transaction.transaction_at <= end_date,
        Transaction.is_deleted == False,
    )
    return query


def get_interwallet_transactions_query(
    user, role, start_date, end_date, query_params={}
):
    """
    Get interwallet transaction query filtered by date range and user permissions
    """
    query = fetch_standard_resources(
        model_class=InterWalletTransaction,
        user=user,
        role=role,
        query_params=query_params,
    )
    query = query.filter(
        InterWalletTransaction.transaction_at >= start_date,
        InterWalletTransaction.transaction_at <= end_date,
        InterWalletTransaction.is_deleted == False,
    )
    return query


def calculate_transaction_totals(query):
    """
    Calculate total credit, debit, and transaction count
    """
    total_credit = (
        query.filter(Transaction.type == TransactionType.CREDIT)
        .with_entities(func.coalesce(func.sum(Transaction.amount), 0))
        .scalar()
    )

    total_debit = (
        query.filter(Transaction.type == TransactionType.DEBIT)
        .with_entities(func.coalesce(func.sum(Transaction.amount), 0))
        .scalar()
    )

    return format(float(total_credit or 0), ".2f"), format(
        float(total_debit or 0), ".2f"
    )


def get_category_summary(transaction_query):
    """
    Calculate category-wise summary of transactions
    """
    category_summary = (
        transaction_query.join(Category)
        .group_by(Category.id, Category.name)
        .with_entities(
            Category.id,
            Category.name,
            func.sum(
                case(
                    (Transaction.type == TransactionType.CREDIT, Transaction.amount),
                    else_=0,
                )
            ).label("total_credit"),
            func.sum(
                case(
                    (Transaction.type == TransactionType.DEBIT, Transaction.amount),
                    else_=0,
                )
            ).label("total_debit"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .all()
    )

    return [
        {
            "category": {"id": str(category.id), "name": category.name},
            "total_credit": format(float(category.total_credit or 0), ".2f"),
            "total_debit": format(float(category.total_debit or 0), ".2f"),
            "transaction_count": category.transaction_count,
        }
        for category in category_summary
    ]


def get_wallet_summary(transaction_query):
    """
    Calculate wallet-wise summary of transactions (without transaction count)
    """
    wallet_summary = (
        transaction_query.join(Wallet, Transaction.wallet_id == Wallet.id)
        .group_by(Wallet.id, Wallet.name)
        .with_entities(
            Wallet.id,
            Wallet.name,
            func.sum(
                case(
                    (Transaction.type == TransactionType.CREDIT, Transaction.amount),
                    else_=0,
                )
            ).label("total_credit"),
            func.sum(
                case(
                    (Transaction.type == TransactionType.DEBIT, Transaction.amount),
                    else_=0,
                )
            ).label("total_debit"),
        )
        .all()
    )

    return [
        {
            "wallet": {"id": str(wallet.id), "name": wallet.name},
            "total_credit": format(float(wallet.total_credit or 0), ".2f"),
            "total_debit": format(float(wallet.total_debit or 0), ".2f"),
        }
        for wallet in wallet_summary
    ]


def generate_transaction_report(current_user, query_params={}):
    """
    Generate a simplified transaction report including:
    - Regular transactions
    - Interwallet transfers
    - Summary totals
    """
    logger.info(
        f"Generating transaction report for user {current_user.id} with params: {query_params}"
    )

    # Parse and validate dates
    start_date, end_date = parse_and_validate_dates(
        query_params.get("start_date"), query_params.get("end_date")
    )

    current_user_role = current_user.role.value

    if current_user.role == UserRole.ADMIN:
        if "user_id" not in query_params:
            raise ValidationError("Admin users must provide a user_id of a normal user")

    # Get transaction query
    transaction_query = get_transactions_query(
        user=current_user,
        role=current_user_role,
        start_date=start_date,
        end_date=end_date,
        query_params=query_params,
    )

    category_summary = get_category_summary(transaction_query)
    wallet_summary = get_wallet_summary(transaction_query)
    total_credit, total_debit = calculate_transaction_totals(transaction_query)

    report = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "total_credit": total_credit,
        "total_debit": total_debit,
        "category_summary": category_summary,
        "wallet_summary": wallet_summary,
    }

    logger.info(f"Transaction report generated successfully. ")
    return report


def get_spending_trends(current_user, query_params={}):
    """
    Generate category-based spending trends for a specified date range.

    Args:
        current_user: The authenticated user
        query_params: Query parameters including start_date, end_date, and user_id for admin

    Returns:
        Dict: Spending trends data organized by category
    """
    logger.info(
        f"Generating spending trends for user {current_user.id} with params: {query_params}"
    )

    start_date, end_date = parse_and_validate_dates(
        query_params.get("start_date"), query_params.get("end_date")
    )

    current_user_role = current_user.role.value

    # Validate admin permission to view other users' data
    if current_user.role == UserRole.ADMIN:
        if "user_id" not in query_params:
            raise ValidationError("Admin users must provide a user_id of a normal user")

    # Get transaction query using existing function
    transaction_query = get_transactions_query(
        user=current_user,
        role=current_user_role,
        start_date=start_date,
        end_date=end_date,
        query_params=query_params,
    )
    total_credit, total_debit = calculate_transaction_totals(transaction_query)

    total_credit = round(float(total_credit or 0), 2)
    total_debit = round(float(total_debit or 0), 2)

    # Get all debit transactions grouped by category
    category_transactions = (
        transaction_query.join(Category, Transaction.category_id == Category.id)
        .filter(Transaction.type == TransactionType.DEBIT)
        .with_entities(
            Category.id,
            Category.name,
            func.sum(Transaction.amount).label("total_amount"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .group_by(Category.id, Category.name)
        .all()
    )
    spending_trends = []

    for result in category_transactions:
        category_id = str(result.id)
        total_amount = round(
            float(result.total_amount or 0), 2
        )  # Convert Decimal to float

        percentage = format(
            ((total_amount / total_debit) * 100 if total_debit > 0 else 0), ".2f"
        )

        spending_trends.append(
            {
                "category": {"id": category_id, "name": result.name},
                "amount": format(total_amount, ".2f"),
                "percentage": percentage,
                "transaction_count": result.transaction_count,
            }
        )
    spending_trends.sort(key=lambda x: x["amount"], reverse=True)

    trends_data = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "total_credit": format(total_credit, ".2f"),
        "total_debit": format(total_debit, ".2f"),
        "spending_trends": spending_trends,
    }
    logger.info(
        f"Spending trends generated successfully with {len(spending_trends)} categories"
    )

    return trends_data
