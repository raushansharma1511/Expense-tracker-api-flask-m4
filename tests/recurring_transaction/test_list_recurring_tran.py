from flask import url_for
from app.models.recurring_transaction import (
    TransactionFrequency,
)


class TestRecurringTransactionList:
    def test_list_own_transactions(
        self, client, auth_headers, recurring_transaction, db_session
    ):
        response = client.get(
            url_for("recurring_transaction.recurring_transactions"),
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == str(recurring_transaction.id)

    def test_list_all_as_admin(
        self, client, admin_headers, recurring_transaction, child_recurring_transaction
    ):
        response = client.get(
            url_for("recurring_transaction.recurring_transactions"),
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["data"]) == 2
        assert any(tx["id"] == str(recurring_transaction.id) for tx in data["data"])
        assert any(
            tx["id"] == str(child_recurring_transaction.id) for tx in data["data"]
        )

    def test_list_child_transactions(
        self, client, auth_headers, child_recurring_transaction
    ):
        response = client.get(
            url_for("recurring_transaction.recurring_transactions")
            + f"?child_id={child_recurring_transaction.user_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == str(child_recurring_transaction.id)

    def test_list_with_filter(self, client, auth_headers, recurring_transaction):
        response = client.get(
            url_for("recurring_transaction.recurring_transactions")
            + f"?frequency={TransactionFrequency.MONTHLY.value}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["data"]) == 1
        assert data["data"][0]["frequency"] == "MONTHLY"

    def test_list_unauthenticated(self, client):
        response = client.get(url_for("recurring_transaction.recurring_transactions"))
        assert response.status_code == 401
        assert "error" in response.get_json()
