from app.models.wallet import Wallet
from flask import url_for


class TestUpdateWallet:
    def test_update_own_wallet(self, client, user_wallet, auth_headers, db_session):
        """Test user updating own wallet name"""
        update_data = {"name": "Updated Wallet"}
        response = client.patch(
            url_for("wallet.wallet-detail", id=user_wallet.id),
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["name"].lower() == "updated wallet".lower()
        db_session.refresh(user_wallet)
        assert user_wallet.name.lower() == "updated wallet".lower()

    def test_admin_update_any_wallet(
        self, client, child_wallet, admin_headers, db_session
    ):
        """Test admin updating any wallet"""
        update_data = {"name": "Admin Updated Wallet"}
        response = client.patch(
            url_for("wallet.wallet-detail", id=child_wallet.id),
            json=update_data,
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["name"].lower() == "admin updated wallet".lower()
        db_session.refresh(child_wallet)
        assert child_wallet.name.lower() == "admin updated wallet".lower()

    def test_update_other_wallet(self, client, test_user2, auth_headers, db_session):
        """Test user updating another’s wallet (should fail, not a child)"""
        wallet2 = Wallet(user_id=test_user2.id, name="Test Wallet 2")
        db_session.add(wallet2)
        db_session.commit()

        update_data = {"name": "Invalid Update"}
        response = client.patch(
            url_for("wallet.wallet-detail", id=wallet2.id),
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "Wallet not found".lower() in data["error"].lower()

    def test_update_wallet_duplicate_name(
        self, client, test_user, user_wallet, auth_headers, db_session
    ):
        """Test updating to duplicate name"""
        second_wallet = Wallet(name="Second wallet", user_id=test_user.id, balance=0.00)
        db_session.add(second_wallet)
        db_session.commit()
        update_data = {"name": "Second wallet"}
        response = client.patch(
            url_for("wallet.wallet-detail", id=user_wallet.id),
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "already exists" in data["error"]["name"].lower()
        db_session.delete(second_wallet)
        db_session.commit()

    def test_update_wallet_empty_name(self, client, user_wallet, auth_headers):
        """Test updating with empty name"""
        update_data = {"name": ""}
        response = client.patch(
            url_for("wallet.wallet-detail", id=user_wallet.id),
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert (
            "Length must be between 1 and 100.".lower() in data["error"]["name"].lower()
        )

    def test_update_deleted_wallet(self, client, user_wallet, auth_headers, db_session):
        """Test updating deleted wallet (should fail)"""
        user_wallet.is_deleted = True
        db_session.commit()
        update_data = {"name": "Updated Deleted Wallet"}
        response = client.patch(
            url_for("wallet.wallet-detail", id=user_wallet.id),
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "Wallet not found" in data["error"]

    def test_child_update_parent_wallet(self, client, user_wallet, child_headers):
        """Test child updating parent’s wallet (should fail)"""
        update_data = {"name": "Child Update"}
        response = client.patch(
            url_for("wallet.wallet-detail", id=user_wallet.id),
            json=update_data,
            headers=child_headers,
        )
        assert response.status_code == 404  # Child has no access
        data = response.get_json()
        assert "Wallet not found" in data["error"]

    def test_parent_update_child_wallet(self, client, child_wallet, auth_headers):
        """Test parent updating child’s wallet (should fail with 403)"""
        update_data = {"name": "Parent Update"}
        response = client.patch(
            url_for("wallet.wallet-detail", id=child_wallet.id),
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 403
        data = response.get_json()
        assert "permission to modify your child resource" in data["error"].lower()
