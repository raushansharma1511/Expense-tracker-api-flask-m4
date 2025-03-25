from flask import url_for
from app.models.interwallet_transaction import InterWalletTransaction


class TestInterWalletTransactionListCreateResource:
    def test_create_transaction_success(
        self, client, auth_headers, interwallet_transaction_data, db_session
    ):
        response = client.post(
            url_for("interwallet_transaction.transactions"),
            json=interwallet_transaction_data,
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.get_json()
        assert "id" in data
        assert data["amount"] == "50.00"
        assert (
            data["source_wallet"]["id"]
            == interwallet_transaction_data["source_wallet_id"]
        )
        # Cleanup
        db_session.query(InterWalletTransaction).filter_by(id=data["id"]).delete()
        db_session.commit()

    def test_create_transaction_as_admin(
        self,
        client,
        admin_headers,
        child_user,
        child_wallet,
        child_second_wallet,
        db_session,
    ):
        data = {
            "user_id": str(child_user.id),
            "source_wallet_id": str(child_second_wallet.id),
            "destination_wallet_id": str(child_wallet.id),
            "amount": "30.00",
            "description": "Admin-created transfer",
        }
        response = client.post(
            url_for("interwallet_transaction.transactions"),
            json=data,
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.get_json()
        assert "id" in data
        assert data["user_id"] == str(child_user.id)
        # Cleanup
        db_session.query(InterWalletTransaction).filter_by(id=data["id"]).delete()
        db_session.commit()

    def test_create_transaction_for_child_as_parent(
        self, client, auth_headers, child_user, child_wallet, child_second_wallet
    ):
        data = {
            "user_id": str(child_user.id),
            "source_wallet_id": str(child_second_wallet.id),
            "destination_wallet_id": str(child_wallet.id),
            "amount": "30.00",
            "description": "Parent transfer for child",
        }
        response = client.post(
            url_for("interwallet_transaction.transactions"),
            json=data,
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "error" in response.get_json()
        assert (
            "You can only create transactions for yourself"
            in response.get_json()["error"]["user_id"]
        )

    def test_create_transaction_invalid_amount(
        self, client, auth_headers, interwallet_transaction_data
    ):
        interwallet_transaction_data["amount"] = "-10.00"
        response = client.post(
            url_for("interwallet_transaction.transactions"),
            json=interwallet_transaction_data,
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "error" in response.get_json()
        assert (
            "Must be greater than or equal to 1"
            in response.get_json()["error"]["amount"]
        )

    def test_create_transaction_same_wallets(
        self, client, auth_headers, interwallet_transaction_data
    ):
        interwallet_transaction_data["destination_wallet_id"] = (
            interwallet_transaction_data["source_wallet_id"]
        )
        response = client.post(
            url_for("interwallet_transaction.transactions"),
            json=interwallet_transaction_data,
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "error" in response.get_json()
        assert (
            "must be different" in response.get_json()["error"]["destination_wallet_id"]
        )

    def test_create_transaction_unauthenticated(
        self, client, interwallet_transaction_data
    ):
        response = client.post(
            url_for("interwallet_transaction.transactions"),
            json=interwallet_transaction_data,
        )
        assert response.status_code == 401
        assert "error" in response.get_json()
        assert "Authorization required" in response.get_json()["error"]
