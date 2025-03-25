from flask import url_for


class TestInterWalletTransactionDetailResource:
    def test_delete_own_transaction(
        self, client, user_interwallet_transaction, auth_headers, db_session
    ):
        response = client.delete(
            url_for(
                "interwallet_transaction.transaction-detail",
                id=user_interwallet_transaction.id,
            ),
            headers=auth_headers,
        )
        assert response.status_code == 204
        assert response.data == b""
        db_session.refresh(user_interwallet_transaction)
        assert user_interwallet_transaction.is_deleted is True

    def test_delete_child_transaction_by_parent(
        self, client, child_interwallet_transaction, auth_headers
    ):
        response = client.delete(
            url_for(
                "interwallet_transaction.transaction-detail",
                id=child_interwallet_transaction.id,
            ),
            headers=auth_headers,
        )
        assert response.status_code == 403
        assert "error" in response.get_json()
        assert (
            "You don't have permission to modify your child resource"
            in response.get_json()["error"]
        )

    def test_delete_other_user_transaction(
        self, client, user_interwallet_transaction, auth_headers_user2
    ):
        response = client.delete(
            url_for(
                "interwallet_transaction.transaction-detail",
                id=user_interwallet_transaction.id,
            ),
            headers=auth_headers_user2,
        )
        assert response.status_code == 404
        assert "error" in response.get_json()
        assert "InterWalletTransaction not found" in response.get_json()["error"]

    def test_delete_transaction_as_admin(
        self, client, child_interwallet_transaction, admin_headers, db_session
    ):
        response = client.delete(
            url_for(
                "interwallet_transaction.transaction-detail",
                id=child_interwallet_transaction.id,
            ),
            headers=admin_headers,
        )
        assert response.status_code == 204
        assert response.data == b""
        db_session.refresh(child_interwallet_transaction)
        assert child_interwallet_transaction.is_deleted is True

    def test_delete_already_deleted_transaction(
        self, client, user_interwallet_transaction, auth_headers, db_session
    ):
        user_interwallet_transaction.is_deleted = True
        db_session.commit()
        response = client.delete(
            url_for(
                "interwallet_transaction.transaction-detail",
                id=user_interwallet_transaction.id,
            ),
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert "error" in response.get_json()
        assert "InterWalletTransaction not found" in response.get_json()["error"]
