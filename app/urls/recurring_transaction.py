from flask import Blueprint
from flask_restful import Api
from app.resources.recurring_transaction import (
    RecurringTransactionListResource,
    RecurringTransactionDetailResource,
)


recurring_transaction_bp = Blueprint("recurring_transaction", __name__)
recurring_transaction_api = Api(recurring_transaction_bp)

recurring_transaction_api.add_resource(
    RecurringTransactionListResource, "", endpoint="recurring_transactions"
)
recurring_transaction_api.add_resource(
    RecurringTransactionDetailResource, "/<id>", endpoint="recurring-transaction-detail"
)
