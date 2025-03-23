from flask_restful import Resource
from flask import request, g, current_app
from marshmallow import ValidationError

from app.extensions import db
from app.models.wallet import Wallet
from app.models.user import User
from app.schemas.wallet import (
    wallet_schema,
    wallets_schema,
    wallet_update_schema,
)
from app.services.wallet import get_user_wallets, delete_wallet
from app.utils.permissions import (
    authenticated_user,
    object_permission,
)
from app.utils.responses import validation_error_response
from app.utils.pagination import paginate
from app.utils.validators import normalize_name
from app.utils.logger import logger


class WalletListCreateResource(Resource):
    """Resource for listing and creating wallets"""

    method_decorators = [authenticated_user]

    def get(self):
        """
        Get wallets based on user role with optional filtering.
        """
        try:
            user = g.user
            user_role = g.role

            query_params = request.args.to_dict()
            logger.info(
                f"Wallet list requested by user {user.id} with params: {query_params}"
            )
            query = get_user_wallets(user, user_role, query_params)

            # Return paginated response
            result = paginate(
                query=query,
                schema=wallets_schema,
                endpoint="wallet.wallet-list-create",
            )
            return result, 200

        except ValidationError as err:
            return validation_error_response(err)

    def post(self):
        """
        Create a new wallet.
        - ADMIN can create wallets for any non-admin user
        - USER and CHILD_USER can only create wallets for themselves
        Balance is always initialized to 0.
        """
        try:
            data = request.get_json() or {}
            logger.info(f"Wallet creation request from user {g.user}: {data}")

            # Validate and create wallet
            wallet = wallet_schema.load(data)

            # Save to database
            db.session.add(wallet)
            db.session.commit()

            logger.info(f"Wallet created successfully: {wallet.id} by user {g.user.id}")

            return wallet_schema.dump(wallet), 201

        except ValidationError as err:
            return validation_error_response(err)


class WalletDetailResource(Resource):
    """
    Resource for retrieving, updating and deleting a specific wallet
        - ADMIN: Can view(even deleted), update and deleted any wallet.
        - USER: Can view own and child's wallets, but can update and delete only its own wallets.
        - CHILD_USER: Can view, update and delete only own wallets
    """

    method_decorators = [object_permission(Wallet), authenticated_user]

    def get(self, id):
        """Get a specific wallet."""
        # Object is already loaded by permission decorator
        wallet = g.object
        result = wallet_schema.dump(wallet)

        logger.info(f"Wallet {wallet.id} retrieved by user {g.user.id}")
        return result, 200

    def patch(self, id):
        """Update a specific wallet's name."""
        try:
            wallet = g.object
            data = request.get_json() or {}

            logger.info(
                f"Wallet update request for {wallet.id} by user {g.user.id}: {data}"
            )
            updated_wallet = wallet_update_schema.load(
                data, instance=wallet, partial=True
            )
            updated_wallet.name = normalize_name(updated_wallet.name)
            db.session.commit()

            logger.info(f"Wallet {wallet.id} updated by user {g.user.id}")
            return wallet_schema.dump(updated_wallet), 200

        except ValidationError as err:
            return validation_error_response(err)

    def delete(self, id):
        """
        Delete (soft delete) a specific wallet.
        - Cannot delete a wallet with non-zero balance and also if any transaction associated with it.
        """
        # Object is already loaded by permission decorator
        try:
            wallet = g.object

            delete_wallet(wallet)

            logger.info(f"Wallet {wallet.id} deleted by user {g.user.id}")
            return "", 204

        except ValidationError as err:
            return validation_error_response(err)
