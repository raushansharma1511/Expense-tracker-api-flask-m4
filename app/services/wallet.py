from flask import g
from app.extensions import db
from app.models.wallet import Wallet
from app.utils.logger import logger
from app.services.common import fetch_standard_resources
from marshmallow.exceptions import ValidationError
from app.models.transaction import Transaction
from app.models.recurring_transaction import RecurringTransaction
from app.models.interwallet_transaction import InterWalletTransaction


def get_user_wallets(user, role, query_params=None):
    """
    Get wallets based on user role and query parameters.

    Args:
        user: The user requesting wallets
        role: The role of the requesting user
        query_params: Dict with optional filters:
            - user_id: For ADMIN to filter by specific user
            - child_id: For USER to filter by their child

    Returns:
        SQLAlchemy query object with appropriate filters
    """
    # Get base query with standard role-based filtering
    query = fetch_standard_resources(
        model_class=Wallet,
        user=user,
        role=role,
        query_params=query_params,
        user_field="user_id",
    )

    # Apply wallet-specific ordering
    query = query.order_by(Wallet.created_at.desc())

    return query


def delete_wallet(wallet):

    if float(wallet.balance) != 0:
        logger.warning(
            f"User {g.user.id} attempted to delete wallet {wallet.id} with non-zero balance"
        )
        raise ValidationError(
            "Cannot delete wallet with non-zero balance. Please transfer all funds first."
        )

    has_transactions = (
        db.session.query(
            db.session.query(Transaction)
            .filter(
                Transaction.wallet_id == wallet.id,
                Transaction.is_deleted == False,
            )
            .exists()
        ).scalar()
        or db.session.query(
            db.session.query(RecurringTransaction)
            .filter(
                RecurringTransaction.wallet_id == wallet.id,
                RecurringTransaction.is_deleted == False,
            )
            .exists()
        ).scalar()
        or db.session.query(
            db.session.query(InterWalletTransaction)
            .filter(
                (
                    (InterWalletTransaction.source_wallet_id == wallet.id)
                    | (InterWalletTransaction.destination_wallet_id == wallet.id)
                ),
                InterWalletTransaction.is_deleted == False,
            )
            .exists()
        ).scalar()
    )

    if has_transactions:
        logger.warning(
            f"User {g.user.id} attempted to delete wallet {wallet.id} with existing transactions"
        )
        raise ValidationError(
            "Cannot delete wallet with existing transactions. "
            "Delete all transactions, recurring transactions, and inter-wallet transactions first."
        )

    # If all checks pass, soft delete the wallet
    wallet.is_deleted = True
    db.session.commit()

    return True
