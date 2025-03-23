from flask import Blueprint
from flask_restful import Api
from app.resources.interwallet_transaction import (
    InterWalletTransactionListCreateResource,
    InterWalletTransactionDetailResource,
)

interwallet_transaction_bp = Blueprint("interwallet_transaction", __name__)
interwallet_transaction_api = Api(interwallet_transaction_bp)

# Register endpoints
interwallet_transaction_api.add_resource(
    InterWalletTransactionListCreateResource, "", endpoint="transactions"
)
interwallet_transaction_api.add_resource(
    InterWalletTransactionDetailResource, "/<id>", endpoint="transaction-detail"
)
