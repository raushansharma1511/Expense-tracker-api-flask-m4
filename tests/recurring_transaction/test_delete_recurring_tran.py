from flask import url_for


class TestRecurringTransactionDelete:
    def test_delete_own_transaction(
        self, client, auth_headers, recurring_transaction, db_session
    ):
        response = client.delete(
            url_for(
                "recurring_transaction.recurring-transaction-detail",
                id=recurring_transaction.id,
            ),
            headers=auth_headers,
        )
        assert response.status_code == 204
        db_session.refresh(recurring_transaction)
        assert recurring_transaction.is_deleted is True

    def test_delete_child_transaction(
        self, client, auth_headers, child_recurring_transaction
    ):
        response = client.delete(
            url_for(
                "recurring_transaction.recurring-transaction-detail",
                id=child_recurring_transaction.id,
            ),
            headers=auth_headers,
        )
        assert response.status_code == 403
        assert "error" in response.get_json()

    def test_delete_other_user_transaction(
        self, client, auth_headers_user2, recurring_transaction
    ):
        response = client.delete(
            url_for(
                "recurring_transaction.recurring-transaction-detail",
                id=recurring_transaction.id,
            ),
            headers=auth_headers_user2,
        )
        assert response.status_code == 404

    def test_delete_as_admin(
        self, client, admin_headers, child_recurring_transaction, db_session
    ):
        response = client.delete(
            url_for(
                "recurring_transaction.recurring-transaction-detail",
                id=child_recurring_transaction.id,
            ),
            headers=admin_headers,
        )
        assert response.status_code == 204
        db_session.refresh(child_recurring_transaction)
        assert child_recurring_transaction.is_deleted is True

    def test_delete_already_deleted(
        self, client, auth_headers, recurring_transaction, db_session
    ):
        recurring_transaction.is_deleted = True
        db_session.commit()
        response = client.delete(
            url_for(
                "recurring_transaction.recurring-transaction-detail",
                id=recurring_transaction.id,
            ),
            headers=auth_headers,
        )
        assert response.status_code == 404
