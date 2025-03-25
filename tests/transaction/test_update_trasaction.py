import uuid
import pytest
from datetime import datetime, timezone
from flask import url_for
from app.models.transaction import Transaction, TransactionType


class TestTransactionDetailResource:
    """Tests for transaction detail operations (get, update, delete)"""

    @pytest.fixture(autouse=True)
    def mock_check_budget_thresholds(self, mocker):
        """
        Mock the check_budget_thresholds.delay call for all tests in this class.
        """
        mock = mocker.patch("app.services.manage_budget.check_budget_thresholds.delay")
        mock.return_value = None
        return mock

    def test_update_own_transaction(
        self,
        client,
        user_transaction,
        user_wallet,
        predefined_category,
        auth_headers,
        mock_check_budget,
        db_session,
    ):
        update_data = {"amount": "75.00", "description": "Updated"}
        url = url_for("transaction.transaction-detail", id=str(user_transaction.id))
        response = client.patch(url, json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert float(data["amount"]) == 75.00
        db_session.refresh(user_wallet)
        assert float(user_wallet.balance) == -75.00  # Should be -75 if app fixed

    def test_admin_update_any_transaction(
        self,
        client,
        child_transaction,
        child_wallet,
        predefined_category,
        admin_headers,
        mock_check_budget,
        db_session,
    ):
        update_data = {"amount": "40.00"}
        url = url_for("transaction.transaction-detail", id=str(child_transaction.id))
        response = client.patch(url, json=update_data, headers=admin_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert float(data["amount"]) == 40.00
        db_session.refresh(child_wallet)
        assert float(child_wallet.balance) == -40.00  # Should be -40 if app fixed

    def test_parent_update_child_transaction(
        self, client, child_transaction, auth_headers
    ):
        update_data = {"amount": "40.00"}
        url = url_for("transaction.transaction-detail", id=str(child_transaction.id))
        response = client.patch(url, json=update_data, headers=auth_headers)
        assert response.status_code == 403
        assert (
            "permission to modify your child resource"
            in response.get_json()["error"].lower()
        )

    def test_update_invalid_amount(self, client, user_transaction, auth_headers):
        update_data = {"amount": "-10.00"}
        url = url_for("transaction.transaction-detail", id=str(user_transaction.id))
        response = client.patch(url, json=update_data, headers=auth_headers)
        assert response.status_code == 400
        assert "amount" in response.get_json()["error"]

    def test_update_type_change(
        self,
        client,
        user_transaction,
        user_wallet,
        auth_headers,
        mock_check_budget,
        db_session,
    ):
        update_data = {"type": "CREDIT"}
        url = url_for("transaction.transaction-detail", id=str(user_transaction.id))
        response = client.patch(url, json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["type"] == "CREDIT"
        db_session.refresh(user_wallet)
        assert float(user_wallet.balance) == 50.00

    def test_update_other_user_transaction(
        self,
        client,
        test_user,
        test_user2,
        user_wallet,
        user_category,
        auth_headers,
        db_session,
    ):
        """Test that a user cannot update another user's transaction at the same level."""
        other_transaction = Transaction(
            id=uuid.uuid4(),
            user_id=test_user2.id,  # Owned by test_user2
            wallet_id=user_wallet.id,
            category_id=user_category.id,
            amount=20.00,
            type=TransactionType.DEBIT,
            transaction_at=datetime.now(timezone.utc),
            description="Other user's expense",
        )
        db_session.add(other_transaction)
        db_session.commit()

        # test_user tries to update test_user2's transaction
        update_data = {"amount": "30.00", "description": "Unauthorized update"}
        url = url_for("transaction.transaction-detail", id=str(other_transaction.id))
        response = client.patch(url, json=update_data, headers=auth_headers)
        assert response.status_code == 404
        assert "Transaction not found" in response.get_json()["error"]

        # Cleanup
        db_session.delete(other_transaction)
        db_session.commit()
