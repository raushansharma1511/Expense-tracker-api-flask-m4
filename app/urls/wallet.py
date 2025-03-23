from flask import Blueprint
from flask_restful import Api
from app.resources.wallet import WalletListCreateResource, WalletDetailResource

wallet_bp = Blueprint("wallet", __name__)
wallet_api = Api(wallet_bp)

# Register endpoints
wallet_api.add_resource(WalletListCreateResource, "", endpoint="wallet-list-create")
wallet_api.add_resource(WalletDetailResource, "/<id>", endpoint="wallet-detail")
