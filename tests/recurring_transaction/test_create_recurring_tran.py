from datetime import datetime, timedelta, timezone
from flask import url_for


class TestRecurringTransactionCreate:
    def test_create_success(
        self, client, auth_headers, test_user, user_wallet, user_category
    ):
        data = {
            "amount": 25.00,
            "description": "Weekly subscription",
            "type": "DEBIT",
            "frequency": "WEEKLY",
            "start_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "user_id": str(test_user.id),
            "wallet_id": str(user_wallet.id),
            "category_id": str(user_category.id),
        }
        response = client.post(
            url_for("recurring_transaction.recurring_transactions"),
            json=data,
            headers=auth_headers,
        )
        assert response.status_code == 201
        result = response.get_json()
        assert result["amount"] == "25.00"
        assert result["frequency"] == "WEEKLY"

    def test_create_as_admin_for_user(
        self, client, admin_headers, test_user, user_wallet, user_category
    ):
        data = {
            "amount": 30.00,
            "type": "CREDIT",
            "frequency": "MONTHLY",
            "start_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "user_id": str(test_user.id),
            "wallet_id": str(user_wallet.id),
            "category_id": str(user_category.id),
        }
        response = client.post(
            url_for("recurring_transaction.recurring_transactions"),
            json=data,
            headers=admin_headers,
        )
        assert response.status_code == 201
        result = response.get_json()
        assert result["user_id"] == str(test_user.id)

    def test_create_for_child_as_parent(
        self, client, auth_headers, child_user, child_wallet, user_category
    ):
        data = {
            "amount": 15.00,
            "type": "DEBIT",
            "frequency": "DAILY",
            "start_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "user_id": str(child_user.id),
            "wallet_id": str(child_wallet.id),
            "category_id": str(user_category.id),
        }
        response = client.post(
            url_for("recurring_transaction.recurring_transactions"),
            json=data,
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "error" in response.get_json()
        assert (
            "You can only create recurring transactions for yourself"
            in response.get_json()["error"]["user_id"]
        )

    def test_create_invalid_amount(
        self, client, auth_headers, test_user, user_wallet, user_category
    ):
        data = {
            "amount": 0.50,  # Below min_val (1)
            "type": "DEBIT",
            "frequency": "WEEKLY",
            "start_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "user_id": str(test_user.id),
            "wallet_id": str(user_wallet.id),
            "category_id": str(user_category.id),
        }
        response = client.post(
            url_for("recurring_transaction.recurring_transactions"),
            json=data,
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "error" in response.get_json()
        assert "amount" in response.get_json()["error"]

    def test_create_past_start_at(
        self, client, auth_headers, test_user, user_wallet, user_category
    ):
        data = {
            "amount": 10.00,
            "type": "DEBIT",
            "frequency": "DAILY",
            "start_at": (
                datetime.now(timezone.utc) - timedelta(days=1)
            ).isoformat(),  # Past date
            "user_id": str(test_user.id),
            "wallet_id": str(user_wallet.id),
            "category_id": str(user_category.id),
        }
        response = client.post(
            url_for("recurring_transaction.recurring_transactions"),
            json=data,
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "error" in response.get_json()
        assert "start_at" in response.get_json()["error"]

    def test_create_unauthenticated(
        self, client, test_user, user_wallet, user_category
    ):
        data = {
            "amount": 20.00,
            "type": "CREDIT",
            "frequency": "MONTHLY",
            "start_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "user_id": str(test_user.id),
            "wallet_id": str(user_wallet.id),
            "category_id": str(user_category.id),
        }
        response = client.post(
            url_for("recurring_transaction.recurring_transactions"), json=data
        )
        assert response.status_code == 401
