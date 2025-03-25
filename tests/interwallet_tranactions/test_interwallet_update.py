from flask import url_for


class TestInterWalletTransactionDetailResource:
    def test_update_own_transaction(
        self, client, user_interwallet_transaction, auth_headers
    ):
        update_data = {"amount": "75.00"}
        response = client.patch(
            url_for(
                "interwallet_transaction.transaction-detail",
                id=user_interwallet_transaction.id,
            ),
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["amount"] == "75.00"

    def test_update_child_transaction_by_parent(
        self, client, child_interwallet_transaction, auth_headers
    ):
        update_data = {"amount": "40.00"}
        response = client.patch(
            url_for(
                "interwallet_transaction.transaction-detail",
                id=child_interwallet_transaction.id,
            ),
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 403
        assert "error" in response.get_json()
        assert (
            "You don't have permission to modify your child resource"
            in response.get_json()["error"]
        )

    def test_update_other_user_transaction(
        self, client, user_interwallet_transaction, auth_headers_user2
    ):
        update_data = {"amount": "75.00"}
        response = client.patch(
            url_for(
                "interwallet_transaction.transaction-detail",
                id=user_interwallet_transaction.id,
            ),
            json=update_data,
            headers=auth_headers_user2,
        )
        assert response.status_code == 404
        assert "error" in response.get_json()
        assert "InterWalletTransaction not found" in response.get_json()["error"]

    def test_update_transaction_as_admin(
        self, client, child_interwallet_transaction, admin_headers
    ):
        update_data = {"amount": "40.00"}
        response = client.patch(
            url_for(
                "interwallet_transaction.transaction-detail",
                id=child_interwallet_transaction.id,
            ),
            json=update_data,
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["amount"] == "40.00"

    def test_update_transaction_invalid_amount(
        self, client, user_interwallet_transaction, auth_headers
    ):
        update_data = {"amount": "-10.00"}
        response = client.patch(
            url_for(
                "interwallet_transaction.transaction-detail",
                id=user_interwallet_transaction.id,
            ),
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "error" in response.get_json()
        assert (
            "Must be greater than or equal to 1"
            in response.get_json()["error"]["amount"]
        )
