from flask import url_for


class TestInterWalletTransactionDetailResource:
    def test_get_own_transaction(
        self, client, user_interwallet_transaction, auth_headers
    ):
        response = client.get(
            url_for(
                "interwallet_transaction.transaction-detail",
                id=user_interwallet_transaction.id,
            ),
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == str(user_interwallet_transaction.id)
        assert data["amount"] == "50.00"

    def test_get_child_transaction_by_parent(
        self, client, child_interwallet_transaction, auth_headers
    ):
        response = client.get(
            url_for(
                "interwallet_transaction.transaction-detail",
                id=child_interwallet_transaction.id,
            ),
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == str(child_interwallet_transaction.id)

    def test_get_other_user_transaction(
        self, client, user_interwallet_transaction, auth_headers_user2
    ):
        response = client.get(
            url_for(
                "interwallet_transaction.transaction-detail",
                id=user_interwallet_transaction.id,
            ),
            headers=auth_headers_user2,
        )
        assert response.status_code == 404
        assert "error" in response.get_json()
        assert "InterWalletTransaction not found" in response.get_json()["error"]

    def test_get_transaction_as_admin(
        self, client, child_interwallet_transaction, admin_headers
    ):
        response = client.get(
            url_for(
                "interwallet_transaction.transaction-detail",
                id=child_interwallet_transaction.id,
            ),
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == str(child_interwallet_transaction.id)

    def test_get_deleted_transaction(
        self, client, user_interwallet_transaction, auth_headers, db_session
    ):
        user_interwallet_transaction.is_deleted = True
        db_session.commit()
        response = client.get(
            url_for(
                "interwallet_transaction.transaction-detail",
                id=user_interwallet_transaction.id,
            ),
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert "error" in response.get_json()
        assert "InterWalletTransaction not found" in response.get_json()["error"]
