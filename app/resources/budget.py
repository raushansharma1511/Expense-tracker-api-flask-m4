from flask_restful import Resource
from flask import request, g
from marshmallow import ValidationError
import copy

from app.extensions import db
from app.models.budget import Budget
from app.schemas.budget import budget_schema, budgets_schema, budget_update_schema
from app.services.budget import (
    get_user_budgets,
    create_budget,
    update_budget,
)
from app.utils.permissions import authenticated_user, object_permission
from app.utils.responses import validation_error_response
from app.utils.pagination import paginate
from app.utils.logger import logger


class BudgetListResource(Resource):
    """Resource for listing and creating budgets"""

    method_decorators = [authenticated_user]

    def get(self):
        """
        Get budgets based on user role with optional filtering.
        Query parameters:
        - user_id: For admin to filter by specific user
        - child_id: For regular users to filter by their child
        - category_id: Filter by specific category
        - month: Filter by month (1-12)
        - year: Filter by year
        """
        try:
            # Get authenticated user info
            user = g.user
            user_role = g.role

            query_params = {
                "user_id": request.args.get("user_id"),
                "child_id": request.args.get("child_id"),
                "category_id": request.args.get("category_id"),
                "month": request.args.get("month"),
                "year": request.args.get("year"),
            }

            logger.info(f"Budget list requested by user {user.id}")

            query = get_user_budgets(user, user_role, query_params)

            # Return paginated response
            result = paginate(
                query=query,
                schema=budgets_schema,
                endpoint="budget.budgets",
            )
            return result, 200

        except ValidationError as err:
            return validation_error_response(err)

    def post(self):
        """
        Create a new budget.
        """
        try:
            data = request.get_json() or {}

            logger.info("Creating budget")

            budget = budget_schema.load(data)

            # Create budget through service
            budget = create_budget(budget)

            if isinstance(budget, tuple) and len(budget) == 2:
                return budget

            return budget_schema.dump(budget), 201

        except ValidationError as err:
            return validation_error_response(err)


class BudgetDetailResource(Resource):
    """
    Resource for retrieving, updating and deleting a specific budget
        -ADMIN can view, update and delete any budget
        -USER can view, update and delete their own budgets and can view its child budgets
        -CHILD can view, update and delete their own budgets
    """

    method_decorators = [
        object_permission(Budget),
        authenticated_user,
    ]

    def get(self, id):
        """
        Get a specific budget.
        """
        budget = g.object  # Already has permission checked
        result = budget_schema.dump(budget)
        logger.info(f"Retrieved budget {budget.id}")
        return result, 200

    def patch(self, id):
        """
        Update a specific budget(only amount of the budget can be updated).
        """
        try:
            budget = g.object  # Already has permission checked
            data = request.get_json() or {}

            old_budget = copy.deepcopy(budget)

            logger.info(f"Updating budget {budget.id}")

            updated_budget = budget_update_schema.load(
                data, instance=budget, partial=True
            )

            budget = update_budget(updated_budget, old_budget)

            if isinstance(budget, tuple) and len(budget) == 2:
                return budget

            logger.info(f"Updated budget {budget.id}")
            return budget_schema.dump(budget), 200

        except ValidationError as err:
            return validation_error_response(err)

    def delete(self, id):
        """
        Delete (soft-delete) a specific budget.
        """
        budget = g.object  # Already has permission checked

        budget.is_deleted = True
        db.session.commit()

        logger.info(f"Deleted budget {budget.id}")
        return "", 204
