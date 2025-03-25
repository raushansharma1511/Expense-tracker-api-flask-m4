import uuid
import pytest
from datetime import datetime, timezone
from flask import url_for
from app.models.transaction import Transaction, TransactionType


class TestTransactionDelete:
    """Tests for transaction detail operations (get, update, delete)"""

    @pytest.fixture(autouse=True)
    def mock_check_budget_thresholds(self, mocker):
        """
        Mock the check_budget_thresholds.delay call for all tests in this class.
        """
        mock = mocker.patch("app.services.manage_budget.check_budget_thresholds.delay")
        mock.return_value = None
        return mock

    def test_delete_own_transaction(
        self,
        client,
        user_transaction,
        user_wallet,
        auth_headers,
        db_session,
    ):
        url = url_for("transaction.transaction-detail", id=str(user_transaction.id))
        response = client.delete(url, headers=auth_headers)
        assert response.status_code == 204
        db_session.refresh(user_transaction)
        assert user_transaction.is_deleted is True
        db_session.refresh(user_wallet)
        assert float(user_wallet.balance) == 0.00

    def test_admin_delete_any_transaction(
        self,
        client,
        child_transaction,
        child_wallet,
        admin_headers,
        db_session,
    ):
        url = url_for("transaction.transaction-detail", id=str(child_transaction.id))
        response = client.delete(url, headers=admin_headers)
        assert response.status_code == 204
        db_session.refresh(child_transaction)
        assert child_transaction.is_deleted is True
        db_session.refresh(child_wallet)
        assert float(child_wallet.balance) == 0.00  # -30 to 0 if app fixed

    def test_parent_delete_child_transaction(
        self, client, child_transaction, auth_headers
    ):
        url = url_for("transaction.transaction-detail", id=str(child_transaction.id))
        response = client.delete(url, headers=auth_headers)
        assert response.status_code == 403
        assert (
            "permission to modify your child resource"
            in response.get_json()["error"].lower()
        )

    def test_delete_already_deleted(
        self, client, user_transaction, auth_headers, db_session
    ):
        user_transaction.is_deleted = True
        db_session.commit()
        url = url_for("transaction.transaction-detail", id=str(user_transaction.id))
        response = client.delete(url, headers=auth_headers)
        assert response.status_code == 404
        assert "Transaction not found" in response.get_json()["error"]

    def test_delete_unauthenticated(self, client, user_transaction):
        url = url_for("transaction.transaction-detail", id=str(user_transaction.id))
        response = client.delete(url)
        assert response.status_code == 401

    def test_delete_other_user_transaction(
        self, client, test_user2, user_wallet, user_category, auth_headers, db_session
    ):
        other_transaction = Transaction(
            id=uuid.uuid4(),
            user_id=test_user2.id,  # Owned by test_user2
            wallet_id=user_wallet.id,
            category_id=user_category.id,
            amount=25.00,
            type=TransactionType.DEBIT,
            transaction_at=datetime.now(timezone.utc),
            description="Peer user expense",
        )
        db_session.add(other_transaction)
        db_session.commit()
        url = url_for("transaction.transaction-detail", id=str(other_transaction.id))
        response = client.delete(url, headers=auth_headers)  # test_user's auth
        assert response.status_code == 404
        assert "Transaction not found" in response.get_json()["error"]
        db_session.delete(other_transaction)
        db_session.commit()
