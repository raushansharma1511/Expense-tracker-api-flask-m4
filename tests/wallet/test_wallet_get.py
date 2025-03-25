import uuid
from app.models.wallet import Wallet
from flask import url_for


class TestGetWallet:
    """Tests for wallet detail operations (get, update, delete)"""

    def test_get_own_wallet(self, client, user_wallet, auth_headers):
        """Test user getting own wallet"""
        response = client.get(
            url_for("wallet.wallet-detail", id=user_wallet.id), headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == str(user_wallet.id)
        assert data["name"] == user_wallet.name

    def test_get_child_wallet_by_parent(self, client, child_wallet, auth_headers):
        """Test parent getting child’s wallet"""
        response = client.get(
            url_for("wallet.wallet-detail", id=child_wallet.id), headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == str(child_wallet.id)

    def test_get_other_user_wallet(self, client, test_user2, auth_headers, db_session):
        """Test user getting another’s wallet (should fail)"""
        wallet2 = Wallet(user_id=test_user2.id, name="Test Wallet 2")
        db_session.add(wallet2)
        db_session.commit()
        db_session.refresh(wallet2)

        response = client.get(
            url_for("wallet.wallet-detail", id=wallet2.id), headers=auth_headers
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "Wallet not found".lower() in data["error"].lower()

    def test_admin_get_any_wallet(self, client, child_wallet, admin_headers):
        """Test admin getting any wallet"""
        response = client.get(
            url_for("wallet.wallet-detail", id=child_wallet.id), headers=admin_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == str(child_wallet.id)

    def test_get_nonexistent_wallet(self, client, auth_headers):
        """Test getting nonexistent wallet"""
        nonexistent_id = uuid.uuid4()
        response = client.get(
            url_for("wallet.wallet-detail", id=nonexistent_id), headers=auth_headers
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "Wallet not found" in data["error"]

    def test_get_deleted_wallet_as_user(
        self, client, user_wallet, auth_headers, db_session
    ):
        """Test user getting own deleted wallet (should fail)"""
        user_wallet.is_deleted = True
        db_session.commit()
        response = client.get(
            url_for("wallet.wallet-detail", id=user_wallet.id), headers=auth_headers
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "Wallet not found" in data["error"]

    def test_get_deleted_wallet_as_admin(
        self, client, user_wallet, admin_headers, db_session
    ):
        """Test admin getting deleted wallet"""
        user_wallet.is_deleted = True
        db_session.commit()
        response = client.get(
            url_for("wallet.wallet-detail", id=user_wallet.id), headers=admin_headers
        )
        assert response.status_code == 200  # Admin can see deleted wallets
        data = response.get_json()
        assert data["is_deleted"] is True

    def test_get_wallet_unauthenticated(self, client, user_wallet):
        """Test getting wallet without authentication"""
        response = client.get(url_for("wallet.wallet-detail", id=user_wallet.id))
        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data
