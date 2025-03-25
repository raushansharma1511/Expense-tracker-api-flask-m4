import pytest
from flask import url_for


class TestTransactionCreate:
    """Tests for transaction listing and creation"""

    @pytest.fixture(autouse=True)
    def mock_check_budget_thresholds(self, mocker):
        """
        Mock the check_budget_thresholds.delay call for all tests in this class.
        """
        mock = mocker.patch("app.services.manage_budget.check_budget_thresholds.delay")
        mock.return_value = None
        return mock

    def test_create_transaction_expense(
        self,
        client,
        test_user,
        user_wallet,
        predefined_category,
        auth_headers,
        db_session,
    ):
        data = {
            "user_id": str(test_user.id),
            "wallet_id": str(user_wallet.id),
            "category_id": str(predefined_category.id),
            "amount": "50.00",
            "type": "DEBIT",
            "description": "Test expense",
        }
        url = url_for("transaction.transactions")  # Correct endpoint from route table
        response = client.post(url, json=data, headers=auth_headers)
        assert response.status_code == 201
        data = response.get_json()
        assert data["type"] == "DEBIT"
        assert float(data["amount"]) == 50.00
        db_session.refresh(user_wallet)
        assert float(user_wallet.balance) == -50.00  # No fixture interference

    def test_create_transaction_income(
        self,
        client,
        test_user,
        user_wallet,
        predefined_category,
        auth_headers,
        db_session,
    ):
        data = {
            "user_id": str(test_user.id),
            "wallet_id": str(user_wallet.id),
            "category_id": str(predefined_category.id),
            "amount": "100.00",
            "type": "CREDIT",
            "description": "Test income",
        }
        url = url_for("transaction.transactions")  # Correct endpoint from route table
        response = client.post(url, json=data, headers=auth_headers)
        assert response.status_code == 201
        data = response.get_json()
        assert data["type"] == "CREDIT"
        db_session.refresh(user_wallet)
        assert float(user_wallet.balance) == 100.00

    def test_create_transaction_missing_amount(
        self, client, test_user, user_wallet, predefined_category, auth_headers
    ):
        data = {
            "user_id": str(test_user.id),
            "wallet_id": str(user_wallet.id),
            "category_id": str(predefined_category.id),
            "type": "DEBIT",
        }
        url = url_for("transaction.transactions")  # Correct endpoint from route table
        response = client.post(url, json=data, headers=auth_headers)
        assert response.status_code == 400
        assert "amount" in response.get_json()["error"]

    def test_create_transaction_invalid_amount(
        self, client, test_user, user_wallet, predefined_category, auth_headers
    ):
        data = {
            "user_id": str(test_user.id),
            "wallet_id": str(user_wallet.id),
            "category_id": str(predefined_category.id),
            "amount": "-10.00",
            "type": "DEBIT",
        }
        url = url_for("transaction.transactions")  # Correct endpoint from route table
        response = client.post(url, json=data, headers=auth_headers)
        assert response.status_code == 400
        assert "amount" in response.get_json()["error"]

    def test_create_transaction_for_other_user(
        self, client, child_user, user_wallet, predefined_category, auth_headers
    ):
        data = {
            "user_id": str(child_user.id),
            "wallet_id": str(user_wallet.id),
            "category_id": str(predefined_category.id),
            "amount": "50.00",
            "type": "DEBIT",
        }
        url = url_for("transaction.transactions")  # Correct endpoint from route table
        response = client.post(url, json=data, headers=auth_headers)
        assert response.status_code == 400
        assert (
            "create transactions for yourself"
            in response.get_json()["error"]["user_id"].lower()
        )

    def test_create_transaction_invalid_wallet(
        self, client, test_user, child_wallet, predefined_category, auth_headers
    ):
        data = {
            "user_id": str(test_user.id),
            "wallet_id": str(child_wallet.id),
            "category_id": str(predefined_category.id),
            "amount": "50.00",
            "type": "DEBIT",
        }
        url = url_for("transaction.transactions")  # Correct endpoint from route table
        response = client.post(url, json=data, headers=auth_headers)
        assert response.status_code == 400
        data = response.get_json()
        assert "wallet_id" in data["error"]
        assert "wallet not found".lower() in data["error"]["wallet_id"].lower()

    def test_create_transaction_admin_for_admin(
        self, client, admin_user, user_wallet, predefined_category, admin_headers
    ):
        data = {
            "user_id": str(admin_user.id),
            "wallet_id": str(user_wallet.id),
            "category_id": str(predefined_category.id),
            "amount": "50.00",
            "type": "DEBIT",
        }
        url = url_for("transaction.transactions")  # Correct endpoint from route table
        response = client.post(url, json=data, headers=admin_headers)
        assert response.status_code == 400
        assert (
            "admin users cannot have transactions"
            in response.get_json()["error"]["user_id"].lower()
        )

    def test_create_transaction_unauthenticated(
        self, client, test_user, user_wallet, predefined_category
    ):
        data = {
            "user_id": str(test_user.id),
            "wallet_id": str(user_wallet.id),
            "category_id": str(predefined_category.id),
            "amount": "50.00",
            "type": "DEBIT",
        }
        url = url_for("transaction.transactions")  # Correct endpoint from route table
        response = client.post(url, json=data)
        assert response.status_code == 401

    def test_create_transaction_invalid_category(
        self, client, test_user, user_wallet, child_category, auth_headers
    ):
        data = {
            "user_id": str(test_user.id),
            "wallet_id": str(user_wallet.id),
            "category_id": str(child_category.id),
            "amount": "50.00",
            "type": "DEBIT",
        }
        url = url_for("transaction.transactions")  # Correct endpoint from route table
        response = client.post(url, json=data, headers=auth_headers)
        assert response.status_code == 400
        data = response.get_json()
        assert "category_id" in data["error"]
        assert "category not found".lower() in data["error"]["category_id"].lower()

    def test_create_transaction_missing_type(
        self, client, test_user, user_wallet, predefined_category, auth_headers
    ):
        data = {
            "user_id": str(test_user.id),
            "wallet_id": str(user_wallet.id),
            "category_id": str(predefined_category.id),
            "amount": "50.00",
        }
        url = url_for("transaction.transactions")  # Correct endpoint from route table
        response = client.post(url, json=data, headers=auth_headers)
        assert response.status_code == 400  # Assuming app fixed to validate type
        assert "type" in response.get_json()["error"]
