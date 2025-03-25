import uuid
from datetime import datetime, timezone
from flask import url_for
from app.models.transaction import Transaction, TransactionType


class TestTransactionGet:
    """Tests for transaction detail operations (get, update, delete)"""

    def test_get_own_transaction(self, client, user_transaction, auth_headers):
        url = url_for("transaction.transaction-detail", id=str(user_transaction.id))
        response = client.get(url, headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == str(user_transaction.id)

    def test_get_child_transaction_by_parent(
        self, client, child_transaction, auth_headers
    ):
        url = url_for("transaction.transaction-detail", id=str(child_transaction.id))
        response = client.get(url, headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == str(child_transaction.id)

    def test_get_other_transaction(
        self, client, test_user2, user_wallet, user_category, auth_headers, db_session
    ):
        other_transaction = Transaction(
            user_id=test_user2.id,
            wallet_id=user_wallet.id,
            category_id=user_category.id,
            amount=20.00,
            type=TransactionType.DEBIT,
        )
        db_session.add(other_transaction)
        db_session.commit()
        url = url_for("transaction.transaction-detail", id=str(other_transaction.id))
        response = client.get(url, headers=auth_headers)
        assert response.status_code == 404
        assert "Transaction not found" in response.get_json()["error"]
        db_session.delete(other_transaction)
        db_session.commit()

    def test_get_deleted_transaction(
        self, client, user_transaction, auth_headers, db_session
    ):
        user_transaction.is_deleted = True
        db_session.commit()
        url = url_for("transaction.transaction-detail", id=str(user_transaction.id))
        response = client.get(url, headers=auth_headers)
        assert response.status_code == 404
        assert "Transaction not found" in response.get_json()["error"]

    def test_admin_get_any_transaction(self, client, child_transaction, admin_headers):
        url = url_for("transaction.transaction-detail", id=str(child_transaction.id))
        response = client.get(url, headers=admin_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == str(child_transaction.id)

    def test_get_other_user_transaction(
        self,
        client,
        test_user,
        test_user2,
        user_wallet,
        user_category,
        auth_headers,
        db_session,
    ):
        """Test that a user cannot access another user's transaction at the same level."""
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

        # test_user tries to access test_user2's transaction
        url = url_for("transaction.transaction-detail", id=str(other_transaction.id))
        response = client.get(url, headers=auth_headers)
        assert response.status_code == 404
        assert "Transaction not found" in response.get_json()["error"]

        # Cleanup
        db_session.delete(other_transaction)
        db_session.commit()
