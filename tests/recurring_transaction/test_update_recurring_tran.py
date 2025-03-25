from flask import url_for
from datetime import datetime, timedelta, timezone
import uuid


class TestRecurringTransactionUpdate:
    def test_update_own_transaction(
        self, client, auth_headers, recurring_transaction, db_session
    ):
        update_data = {"amount": 75.00, "description": "Updated bill"}
        response = client.patch(
            url_for(
                "recurring_transaction.recurring-transaction-detail",
                id=recurring_transaction.id,
            ),
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["amount"] == "75.00"
        assert data["description"] == "Updated bill"

    def test_update_child_transaction(
        self, client, auth_headers, child_recurring_transaction
    ):
        update_data = {"amount": 40.00}
        response = client.patch(
            url_for(
                "recurring_transaction.recurring-transaction-detail",
                id=child_recurring_transaction.id,
            ),
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 403
        assert "error" in response.get_json()

    def test_update_other_user_transaction(
        self, client, auth_headers_user2, recurring_transaction
    ):
        update_data = {"amount": 60.00}
        response = client.patch(
            url_for(
                "recurring_transaction.recurring-transaction-detail",
                id=recurring_transaction.id,
            ),
            json=update_data,
            headers=auth_headers_user2,
        )
        assert response.status_code == 404

    def test_update_as_admin(
        self, client, admin_headers, child_recurring_transaction, db_session
    ):
        update_data = {"amount": 45.00}
        response = client.patch(
            url_for(
                "recurring_transaction.recurring-transaction-detail",
                id=child_recurring_transaction.id,
            ),
            json=update_data,
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["amount"] == "45.00"

    def test_update_invalid_data(self, client, auth_headers, recurring_transaction):
        update_data = {
            "amount": -10.00,
            "category_id": uuid.uuid4(),
            "wallet_id": uuid.uuid4(),
        }
        response = client.patch(
            url_for(
                "recurring_transaction.recurring-transaction-detail",
                id=recurring_transaction.id,
            ),
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "error" in response.get_json()
        assert "amount" in response.get_json()["error"]
        assert "category_id" in response.get_json()["error"]
        assert "wallet_id" in response.get_json()["error"]

    def test_update_past_start_at(self, client, auth_headers, recurring_transaction):
        update_data = {
            "start_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        }
        response = client.patch(
            url_for(
                "recurring_transaction.recurring-transaction-detail",
                id=recurring_transaction.id,
            ),
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "error" in response.get_json()
        assert "start_at" in response.get_json()["error"]
