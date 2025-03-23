from flask import Blueprint
from flask_restful import Api
from app.resources.budget import (
    BudgetListResource,
    BudgetDetailResource,
)

budget_bp = Blueprint("budget", __name__)
budget_api = Api(budget_bp)

# Register endpoints
budget_api.add_resource(BudgetListResource, "", endpoint="budgets")
budget_api.add_resource(BudgetDetailResource, "/<id>", endpoint="budget-detail")
