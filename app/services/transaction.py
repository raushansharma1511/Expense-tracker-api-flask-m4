from marshmallow import ValidationError
from datetime import datetime
from app.utils.validators import is_valid_uuid
from app.services.common import fetch_standard_resources
from app.models.wallet import Wallet
from app.utils.enums import TransactionType
from decimal import Decimal
from app.services.manage_budget import (
    update_budget_on_transaction_created,
    update_budget_on_transaction_updated,
    update_budget_on_transaction_deleted,
)
from app.extensions import db
from app.models.transaction import Transaction, TransactionType
from app.utils.logger import logger


def get_user_transactions(user, role, query_params=None):
    """
    Get transactions for a user with optional filters
    - Admin user can see any particular user's transactions by providing user_id
    - Normal user can only see their own transactions and his child_user
        transactions by providing child_id in the query params
    - Child users can see their own transactions only

    Args:
        user: The user requesting transactions
        query_params: Dict with optional filters (type, from_date, to_date, category_id, wallet_id)

    Returns:
        SQLAlchemy query object with appropriate filters
    """
    logger.info(f"Getting transactions for user {user.id} with filters: {query_params}")

    query_params = query_params or {}

    query = fetch_standard_resources(
        model_class=Transaction,
        user=user,
        role=role,
        query_params=query_params,
    )

    query = query.order_by(
        Transaction.transaction_at.desc(), Transaction.created_at.desc()
    )

    # Apply filters if provided
    if "type" in query_params and query_params["type"]:
        try:
            transaction_type = TransactionType(query_params["type"])
        except ValueError:
            raise ValidationError(f"Invalid transaction type: {query_params['type']}")
        query = query.filter(Transaction.type == transaction_type)

    if "category_id" in query_params and query_params["category_id"]:
        category_id = query_params["category_id"]

        if is_valid_uuid(category_id):
            query = query.filter(Transaction.category_id == category_id)
        else:
            raise ValidationError(f"Invalid category_id format {category_id}")

    if "wallet_id" in query_params and query_params["wallet_id"]:
        wallet_id = query_params["wallet_id"]

        if is_valid_uuid(wallet_id):
            query = query.filter(Transaction.wallet_id == wallet_id)
        else:
            raise ValidationError(f"Invalid wallet_id format {wallet_id}")

    if "from_date" in query_params and query_params["from_date"]:
        try:
            from_date = datetime.strptime(query_params["from_date"], "%Y-%m-%d")
            query = query.filter(Transaction.transaction_at >= from_date)
        except ValueError:
            raise ValidationError(
                f"Invalid from_date format: {query_params['from_date']}"
            )

    if "to_date" in query_params and query_params["to_date"]:
        try:
            to_date = datetime.strptime(query_params["to_date"], "%Y-%m-%d")
            # Add 1 day to make it inclusive of the end date
            to_date = datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59)
            query = query.filter(Transaction.transaction_at <= to_date)
        except ValueError:
            raise ValidationError(f"Invalid to_date format: {query_params['to_date']}")

    logger.debug("Transaction query built successfully")
    return query


def create_transaction(transaction):
    """create a transaction"""

    try:
        wallet = db.session.get(Wallet, transaction.wallet_id)
        amount = transaction.amount
        transaction_type = transaction.type

        if transaction_type == TransactionType.CREDIT:
            wallet.update_balance(amount)
        else:
            wallet.update_balance(-amount)

        db.session.add(transaction)
        db.session.flush()

        if transaction.type == TransactionType.DEBIT:
            update_budget_on_transaction_created(transaction)

        db.session.commit()

        return transaction

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating transaction: {e}")
        return {"error": f"Error creating transaction {str(e)}"}, 500


def update_transaction(transaction, old_transaction):
    """Update a transaction"""
    try:
        old_wallet_id = old_transaction.wallet_id
        old_amount = old_transaction.amount
        old_type = old_transaction.type

        new_wallet_id = transaction.wallet_id
        new_amount = transaction.amount
        new_type = transaction.type

        balance_update_needed = (
            str(new_wallet_id) != str(old_wallet_id)
            or new_amount != old_amount
            or old_type != new_type
        )

        if balance_update_needed:
            old_wallet = db.session.get(Wallet, old_wallet_id)

            if old_type == TransactionType.CREDIT:
                old_wallet.update_balance(-old_amount)
            else:
                old_wallet.update_balance(old_amount)

            db.session.flush()

            new_wallet = db.session.get(Wallet, new_wallet_id)

            if new_type == TransactionType.CREDIT:
                new_wallet.update_balance(new_amount)
            else:
                new_wallet.update_balance(-new_amount)

        db.session.flush()

        type_changing = old_type != new_type

        if type_changing:
            if old_type == TransactionType.CREDIT and new_type == TransactionType.DEBIT:
                update_budget_on_transaction_created(transaction)

            elif (
                old_type == TransactionType.DEBIT and new_type == TransactionType.CREDIT
            ):
                update_budget_on_transaction_deleted(old_transaction)

        elif new_type == TransactionType.DEBIT:
            update_budget_on_transaction_updated(transaction, old_transaction)

        db.session.commit()

        logger.info(f"Transaction {transaction.id} updated successfully")
        return transaction

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating transaction: {str(e)}")
        return {"error": f"Failed to update transaction: {str(e)}"}, 500


def delete_transaction(transaction):
    """
    Delete (soft-delete) a transaction and reverse its effects.
    """
    try:
        # Reverse the transaction effects on wallet
        wallet = db.session.get(Wallet, transaction.wallet_id)
        amount = Decimal(str(transaction.amount))

        if transaction.type == TransactionType.CREDIT:
            wallet.update_balance(-amount)
        else:
            wallet.update_balance(amount)

        transaction.is_deleted = True

        if transaction.type == TransactionType.DEBIT:
            update_budget_on_transaction_deleted(transaction)

        db.session.commit()

        return True

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting transaction: {str(e)}")
        return {"error": f"Failed to delete transaction: {str(e)}"}, 500
