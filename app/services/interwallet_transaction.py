from app.models.interwallet_transaction import InterWalletTransaction
from app.utils.logger import logger
from app.extensions import db
from app.services.common import fetch_standard_resources
from app.utils.validators import is_valid_uuid
from datetime import datetime
from sqlalchemy import or_
from app.models.wallet import Wallet


def get_user_interwallet_transactions(user, role, query_params={}):
    """
    Get interwallet transactions based on user role and query parameters.
    """
    # Get base query with standard role-based filtering
    query = fetch_standard_resources(
        model_class=InterWalletTransaction,
        user=user,
        role=role,
        query_params=query_params,
    )

    # Apply default ordering (newest first)
    query = query.order_by(
        InterWalletTransaction.transaction_at.desc(),
        InterWalletTransaction.created_at.desc(),
    )

    # Date range filtering
    if "from_date" in query_params and query_params["from_date"]:
        try:
            from_date = datetime.strptime(query_params["from_date"], "%Y-%m-%d")
            query = query.filter(InterWalletTransaction.transaction_at >= from_date)
        except ValueError:
            logger.warning(f"Invalid from_date format: {query_params['from_date']}")

    if "to_date" in query_params and query_params["to_date"]:
        try:
            to_date = datetime.strptime(query_params["to_date"], "%Y-%m-%d")
            # Add 1 day to make it inclusive of the end date
            to_date = datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59)
            query = query.filter(InterWalletTransaction.transaction_at <= to_date)
        except ValueError:
            logger.warning(f"Invalid to_date format: {query_params['to_date']}")

    return query


def create_interwallet_transaction(transaction):
    try:
        source_wallet = db.session.get(Wallet, transaction.source_wallet_id)
        destination_wallet = db.session.get(Wallet, transaction.destination_wallet_id)
        amount = transaction.amount

        source_wallet.update_balance(-amount)
        destination_wallet.update_balance(amount)
        db.session.add(transaction)
        db.session.commit()

        logger.info(f"Created interwallet transaction {transaction.id}")
        return transaction

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating interwallet transaction: {str(e)}")
        return {"error": f"Failed to create transaction: {str(e)}"}, 500


def update_interwallet_transaction(transaction, old_transaction):
    """
    Update an interwallet transaction and adjust wallet balances if needed.

    Args:
        transaction: Updated InterWalletTransaction object
        old_source_id: The original source wallet ID
        old_dest_id: The original destination wallet ID
        old_amount: The original transaction amount

    Returns:
        transaction: Updated transaction
    """
    try:
        # Get old values
        old_source_id = old_transaction.source_wallet_id
        old_dest_id = old_transaction.destination_wallet_id
        old_amount = old_transaction.amount

        # Get new values
        new_source_id = transaction.source_wallet_id
        new_dest_id = transaction.destination_wallet_id
        new_amount = transaction.amount  # Adjust if you use a getter method

        balance_update_needed = (
            new_source_id != old_source_id
            or new_dest_id != old_dest_id
            or new_amount != old_amount
        )

        if balance_update_needed:
            # Reverse the old transaction
            old_source_wallet = db.session.get(Wallet, old_source_id)
            old_dest_wallet = db.session.get(Wallet, old_dest_id)
            old_source_wallet.update_balance(old_amount)
            old_dest_wallet.update_balance(-old_amount)

            db.session.flush()

            # Apply the new transaction
            new_source_wallet = db.session.get(Wallet, new_source_id)
            new_dest_wallet = db.session.get(Wallet, new_dest_id)
            new_source_wallet.update_balance(-new_amount)
            new_dest_wallet.update_balance(new_amount)

        # Save changes
        db.session.commit()

        logger.info(f"Updated interwallet transaction {transaction.id}")
        return transaction

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating interwallet transaction: {str(e)}")
        return {"error": f"Failed to update transaction: {str(e)}"}, 500
