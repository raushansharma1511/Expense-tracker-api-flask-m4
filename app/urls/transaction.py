from flask import Blueprint
from flask_restful import Api
from app.resources.transaction import TransactionListResource, TransactionDetailResource

transaction_bp = Blueprint("transaction", __name__)
transaction_api = Api(transaction_bp)

# Register endpoints
transaction_api.add_resource(TransactionListResource, "", endpoint="transactions")
transaction_api.add_resource(
    TransactionDetailResource, "/<id>", endpoint="transaction-detail"
)
