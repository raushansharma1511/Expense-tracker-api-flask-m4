from flask_restful import Resource
from flask import g, request
from marshmallow import ValidationError
import copy

from app.extensions import db
from app.models.recurring_transaction import RecurringTransaction
from app.schemas.recurring_transaction import (
    recurring_transaction_schema,
    recurring_transactions_schema,
    recurring_transaction_update_schema,
)
from app.services.recurring_transaction import (
    get_user_recurring_transactions,
    create_recurring_transaction,
    update_recurring_transaction,
)
from app.utils.permissions import authenticated_user, object_permission
from app.utils.responses import validation_error_response
from app.utils.pagination import paginate
from app.utils.logger import logger


class RecurringTransactionListResource(Resource):
    """Resource for listing and creating recurring transactions"""

    method_decorators = [authenticated_user]

    def get(self):
        """Get paginated list of recurring transactions with filtering"""
        try:
            # Get query parameters
            query_params = request.args.to_dict()

            query = get_user_recurring_transactions(g.user, g.role, query_params)

            # Paginate results
            return paginate(
                query,
                recurring_transactions_schema,
                endpoint="recurring_transaction.recurring_transactions",
            )

        except ValidationError as err:
            return validation_error_response(err)

    def post(self):
        """Create a new recurring transaction"""
        try:
            data = request.get_json() or {}

            current_user = g.user

            logger.info(
                f"User {current_user.id} creating recurring transaction: {data}"
            )

            # Validate and create recurring transaction
            recurring_transaction = recurring_transaction_schema.load(data)
            result = create_recurring_transaction(recurring_transaction)

            if isinstance(result, tuple) and len(result) == 2:
                return result

            logger.info(
                f"Recurring transaction created successfully with ID {result.id} by user {current_user.id}"
            )
            return recurring_transaction_schema.dump(result), 201

        except ValidationError as err:
            return validation_error_response(err)


class RecurringTransactionDetailResource(Resource):
    """Resource for retrieving, updating and deleting a recurring transaction"""

    method_decorators = [
        object_permission(RecurringTransaction),
        authenticated_user,
    ]

    def get(self, id):
        """Get a specific recurring transaction"""
        # Object is already loaded by permission decorator
        recurring_transaction = g.object
        from app.services.recurring_transaction import calculate_next_execution_date

        print(
            calculate_next_execution_date(
                recurring_transaction, recurring_transaction.start_at
            )
        )

        logger.info(f"User {g.user.id} retrieved recurring transaction {id}")

        return recurring_transaction_schema.dump(recurring_transaction), 200

    def patch(self, id):
        """Update a specific recurring transaction"""
        try:
            # Object is already loaded by permission decorator
            recurring_transaction = g.object
            data = request.get_json() or {}

            logger.info(f"User {g.user.id} updating recurring transaction {id}: {data}")

            # Validate and update
            updated_transaction = recurring_transaction_update_schema.load(
                data, instance=recurring_transaction, partial=True
            )
            result = update_recurring_transaction(updated_transaction, data)

            if isinstance(result, tuple) and len(result) == 2:
                return result

            return recurring_transaction_schema.dump(result), 200

        except ValidationError as err:
            return validation_error_response(err)

        except Exception as e:
            logger.error(f"Error updating recurring transaction: {str(e)}")
            return {"error": f"Failed to update recurring transaction: {str(e)}"}, 500

    def delete(self, id):
        """Delete a specific recurring transaction"""
        recurring_transaction = g.object

        logger.info(f"User {g.user.id} deleting recurring transaction {id}")

        # Mark as deleted
        recurring_transaction.is_deleted = True
        db.session.commit()

        logger.info(
            f"Recurring transaction {id} deleted successfully by user {g.user.id}"
        )
        return "", 204
