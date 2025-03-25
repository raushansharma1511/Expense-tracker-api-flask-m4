import uuid
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from flask import url_for


class TestDeleteWallet:

    def test_delete_own_wallet(self, client, user_wallet, auth_headers, db_session):
        """Test user deleting own wallet"""
        response = client.delete(
            url_for("wallet.wallet-detail", id=user_wallet.id), headers=auth_headers
        )
        assert response.status_code == 204
        db_session.refresh(user_wallet)
        assert user_wallet.is_deleted is True

    def test_admin_delete_any_wallet(
        self, client, child_wallet, admin_headers, db_session
    ):
        """Test admin deleting any wallet"""
        response = client.delete(
            url_for("wallet.wallet-detail", id=child_wallet.id), headers=admin_headers
        )
        assert response.status_code == 204
        db_session.refresh(child_wallet)
        assert child_wallet.is_deleted is True

    def test_delete_wallet_with_balance(
        self, client, user_wallet, auth_headers, db_session
    ):
        """Test deleting wallet with non-zero balance"""
        user_wallet.update_balance(100.00)  # Balance starts at 0, updated here
        db_session.commit()
        response = client.delete(
            url_for("wallet.wallet-detail", id=user_wallet.id), headers=auth_headers
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "non-zero balance" in data["error"].lower()

    def test_delete_wallet_with_transaction(
        self, client, user_category, user_wallet, auth_headers, db_session
    ):
        """Test deleting wallet with transaction"""
        from app.utils.enums import TransactionType

        transaction = Transaction(
            id=uuid.uuid4(),
            wallet_id=user_wallet.id,
            amount=50.00,
            type=TransactionType.CREDIT,
            description="Test",
            user_id=user_wallet.user_id,
            category_id=user_category.id,
        )
        db_session.add(transaction)
        db_session.commit()
        response = client.delete(
            url_for("wallet.wallet-detail", id=user_wallet.id), headers=auth_headers
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "existing transactions" in data["error"].lower()
        db_session.delete(transaction)
        db_session.commit()

    def test_delete_already_deleted_wallet(
        self, client, user_wallet, auth_headers, db_session
    ):
        """Test deleting already deleted wallet"""
        user_wallet.is_deleted = True
        db_session.commit()
        response = client.delete(
            url_for("wallet.wallet-detail", id=user_wallet.id), headers=auth_headers
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "Wallet not found" in data["error"]

    def test_child_delete_parent_wallet(self, client, user_wallet, child_headers):
        """Test child deleting parent’s wallet (should fail)"""
        response = client.delete(
            url_for("wallet.wallet-detail", id=user_wallet.id), headers=child_headers
        )
        assert response.status_code == 404  # Child has no access
        data = response.get_json()
        assert "Wallet not found" in data["error"]

    def test_delete_other_user_wallet(
        self, client, test_user2, auth_headers, db_session
    ):
        """Test user deleting another’s wallet (should fail, not a child)"""
        wallet2 = Wallet(user_id=test_user2.id, name="Test Wallet 2")
        db_session.add(wallet2)
        db_session.commit()
        response = client.delete(
            url_for("wallet.wallet-detail", id=wallet2.id), headers=auth_headers
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "Wallet not found" in data["error"]

    def test_delete_wallet_unauthenticated(self, client, user_wallet):
        """Test deleting wallet without authentication"""
        response = client.delete(url_for("wallet.wallet-detail", id=user_wallet.id))
        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data

    def test_parent_delete_child_wallet(self, client, child_wallet, auth_headers):
        """Test parent deleting child’s wallet (should fail with 403)"""
        response = client.delete(
            url_for("wallet.wallet-detail", id=child_wallet.id), headers=auth_headers
        )
        assert response.status_code == 403
        data = response.get_json()
        assert "permission to modify your child resource" in data["error"].lower()
