from flask import url_for


class TestRecurringTransactionGet:
    def test_get_own_transaction(self, client, auth_headers, recurring_transaction):
        response = client.get(
            url_for(
                "recurring_transaction.recurring-transaction-detail",
                id=recurring_transaction.id,
            ),
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == str(recurring_transaction.id)
        assert data["amount"] == "50.00"

    def test_get_child_transaction(
        self, client, auth_headers, child_recurring_transaction
    ):
        response = client.get(
            url_for(
                "recurring_transaction.recurring-transaction-detail",
                id=child_recurring_transaction.id,
            ),
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == str(child_recurring_transaction.id)

    def test_get_other_user_transaction(
        self, client, auth_headers_user2, recurring_transaction
    ):
        response = client.get(
            url_for(
                "recurring_transaction.recurring-transaction-detail",
                id=recurring_transaction.id,
            ),
            headers=auth_headers_user2,
        )
        assert response.status_code == 404
        assert "error" in response.get_json()

    def test_get_as_admin(self, client, admin_headers, child_recurring_transaction):
        response = client.get(
            url_for(
                "recurring_transaction.recurring-transaction-detail",
                id=child_recurring_transaction.id,
            ),
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == str(child_recurring_transaction.id)

    def test_get_deleted_transaction(
        self, client, auth_headers, recurring_transaction, db_session
    ):
        recurring_transaction.is_deleted = True
        db_session.commit()
        response = client.get(
            url_for(
                "recurring_transaction.recurring-transaction-detail",
                id=recurring_transaction.id,
            ),
            headers=auth_headers,
        )
        assert response.status_code == 404
