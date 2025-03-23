from flask_restful import Resource
from flask import g, request
from marshmallow import ValidationError
import copy

from app.models.transaction import Transaction
from app.schemas.transaction import (
    transaction_schema,
    transactions_schema,
    transaction_update_schema,
)
from app.services.transaction import (
    get_user_transactions,
    create_transaction,
    update_transaction,
    delete_transaction,
)
from app.utils.permissions import (
    authenticated_user,
    object_permission,
)
from app.utils.responses import validation_error_response
from app.utils.pagination import paginate
from app.utils.logger import logger


class TransactionListResource(Resource):
    """Resource for listing and creating transactions"""

    method_decorators = [authenticated_user]

    def get(self):
        """Get paginated list of transactions with filtering"""
        user = g.user
        user_role = g.role

        # # Get query parameters for filtering
        query_params = request.args.to_dict()

        logger.info(
            f"User {user.id} requested transactions list with filters: {query_params}"
        )
        query = get_user_transactions(user, user_role, query_params)

        # Use pagination utility
        result = paginate(
            query=query, schema=transactions_schema, endpoint="transaction.transactions"
        )

        logger.info(f"Returned transactions to user {user.id}")
        return result, 200

    def post(self):
        """Create a new transaction"""
        try:
            data = request.get_json() or {}

            current_user = g.user

            logger.info(f"User {current_user.id} creating transaction: {data}")

            # Validate and create transaction
            transaction = transaction_schema.load(data)
            result = create_transaction(transaction)

            if isinstance(result, tuple):
                return result

            logger.info(
                f"Transaction created successfully with ID {result.id} by user {current_user.id}"
            )
            return transaction_schema.dump(result), 201

        except ValidationError as err:
            return validation_error_response(err)


class TransactionDetailResource(Resource):
    """Resource for retrieving, updating and deleting a transaction"""

    method_decorators = [
        object_permission(Transaction),
        authenticated_user,
    ]

    def get(self, id):
        """Get a specific transaction"""
        # Object is already loaded by permission decorator
        transaction = g.object

        logger.info(f"User {g.user.id} retrieved transaction {id}")

        return transaction_schema.dump(transaction), 200

    def patch(self, id):
        """Update a specific transaction"""
        try:
            # Object is already loaded by permission decorator
            transaction = g.object
            data = request.get_json() or {}

            logger.info(f"User {g.user.id} updating transaction {id}: {data}")

            old_transaction = copy.deepcopy(transaction)

            updated_transaction = transaction_update_schema.load(
                data, instance=transaction, partial=True
            )
            result = update_transaction(updated_transaction, old_transaction)

            if isinstance(result, tuple):
                return result

            return transaction_schema.dump(result), 200

        except ValidationError as err:
            return validation_error_response(err)

    def delete(self, id):
        """Delete a specific transaction"""

        transaction = g.object

        logger.info(f"User {g.user.id} deleting transaction {id}")

        result = delete_transaction(transaction)

        if isinstance(result, tuple):
            return result

        logger.info(f"Transaction {id} deleted successfully by user {g.user.id}")
        return "", 204
