from flask_restful import Resource
from flask import request, g
from marshmallow import ValidationError
import copy

from app.extensions import db
from app.models.interwallet_transaction import InterWalletTransaction
from app.models.wallet import Wallet
from app.schemas.interwallet_transaction import (
    interwallet_transaction_schema,
    interwallet_transactions_schema,
    interwallet_transaction_update_schema,
)
from app.services.interwallet_transaction import (
    get_user_interwallet_transactions,
    create_interwallet_transaction,
    update_interwallet_transaction,
)
from app.utils.permissions import authenticated_user, object_permission
from app.utils.responses import validation_error_response
from app.utils.pagination import paginate
from app.utils.logger import logger


class InterWalletTransactionListCreateResource(Resource):
    """Resource for listing and creating interwallet transactions"""

    method_decorators = [authenticated_user]

    def get(self):
        """
        Get interwallet transactions based on user role with optional filtering.
        """
        try:
            user = g.user
            user_role = g.role

            # Get query parameters
            query_params = {
                "user_id": request.args.get("user_id"),
                "child_id": request.args.get("child_id"),
                "from_date": request.args.get("from_date"),
                "to_date": request.args.get("to_date"),
            }
            logger.info(f"InterWalletTransaction list requested by user {user.id}")
            # Get filtered transactions
            query = get_user_interwallet_transactions(user, user_role, query_params)

            # Return paginated response
            result = paginate(
                query=query,
                schema=interwallet_transactions_schema,
                endpoint="interwallet_transaction.transactions",
            )
            return result, 200
        except ValidationError as err:
            return validation_error_response(err)

    def post(self):
        """Create a new interwallet transaction"""
        try:
            data = request.get_json() or {}

            logger.info(f"Creating interwallet transaction")

            transaction = interwallet_transaction_schema.load(data)

            result = create_interwallet_transaction(transaction)
            if isinstance(result, tuple):
                return result

            return interwallet_transaction_schema.dump(result), 201

        except ValidationError as err:
            return validation_error_response(err)


class InterWalletTransactionDetailResource(Resource):
    """Resource for retrieving, updating and deleting a specific interwallet transaction"""

    method_decorators = [
        object_permission(InterWalletTransaction),
        authenticated_user,
    ]

    def get(self, id):
        """Get a specific interwallet transaction"""
        transaction = g.object
        result = interwallet_transaction_schema.dump(transaction)
        logger.info(f"Retrieved interwallet transaction {transaction.id}")
        return result, 200

    def patch(self, id):
        """Update a specific interwallet transaction"""
        try:
            transaction = g.object
            data = request.get_json() or {}

            old_source_id = transaction.source_wallet_id
            old_dest_id = transaction.destination_wallet_id
            old_amount = transaction.amount

            old_transaction = copy.deepcopy(transaction)

            logger.info(f"Updating interwallet transaction {transaction.id}")

            updated_transaction = interwallet_transaction_update_schema.load(
                data, instance=transaction, partial=True
            )

            result = update_interwallet_transaction(
                updated_transaction, old_transaction
            )
            if isinstance(result, tuple):
                return result

            return interwallet_transaction_schema.dump(result), 200

        except ValidationError as err:
            return validation_error_response(err)

    def delete(self, id):
        """Delete (soft-delete) a specific interwallet transaction"""

        transaction: InterWalletTransaction = g.object

        try:
            # Reverse transaction effect on wallets
            transaction.reverse_from_wallets()

            transaction.is_deleted = True
            db.session.commit()

            logger.info(f"Deleted interwallet transaction {transaction.id}")
            return "", 204

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting interwallet transaction: {str(e)}")
            return {"error": f"Failed to delete transaction: {str(e)}"}, 500
