import uuid
from app.models.wallet import Wallet
from app.models.user import User
from flask import url_for


class TestWalletListResource:
    """Tests for wallet listing and creation"""

    def test_list_wallets_as_admin_all_wallets(
        self, client, admin_user, admin_headers, user_wallet, child_wallet
    ):
        """Test admin lists all wallets"""
        response = client.get(
            url_for("wallet.wallet-list-create"), headers=admin_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert "total_items" in data
        assert "current_page" in data
        assert "total_pages" in data
        assert "per_page" in data

        wallets = data["data"]
        assert len(wallets) >= 2
        assert any(w["id"] == str(user_wallet.id) for w in wallets)
        assert any(w["id"] == str(child_wallet.id) for w in wallets)

    def test_list_specific_user_wallets_as_admin(
        self, client, admin_headers, user_wallet
    ):
        """Test admin lists only user wallets"""
        response = client.get(
            f"{url_for('wallet.wallet-list-create')}?user_id={user_wallet.user_id}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        wallets = data["data"]
        assert len(wallets) >= 1
        assert all(w["user_id"] == str(user_wallet.user_id) for w in wallets)

    def test_list_wallets_as_user_own_only(
        self, client, test_user, auth_headers, user_wallet, child_wallet
    ):
        """Test user lists only own wallets"""
        response = client.get(
            url_for("wallet.wallet-list-create"), headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        wallets = data["data"]
        assert len(wallets) >= 1
        assert any(w["id"] == str(user_wallet.id) for w in wallets)
        assert not any(w["id"] == str(child_wallet.id) for w in wallets)

    def test_list_wallets_as_child_own_only(
        self, client, child_user, child_headers, user_wallet, child_wallet
    ):
        """Test child lists only own wallets"""
        response = client.get(
            url_for("wallet.wallet-list-create"), headers=child_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        wallets = data["data"]
        assert len(wallets) >= 1
        for w in wallets:
            assert w["user_id"] == str(child_user.id)

    def test_list_child_wallets_by_parent(
        self, client, test_user, auth_headers, child_user, child_wallet
    ):
        """Test parent lists child’s wallets"""
        response = client.get(
            f"{url_for('wallet.wallet-list-create')}?child_id={child_user.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        wallets = data["data"]
        assert len(wallets) >= 1
        assert any(w["id"] == str(child_wallet.id) for w in wallets)

    def test_list_wallets_unauthenticated(self, client, user_wallet):
        """Test listing wallets without authentication"""
        response = client.get(url_for("wallet.wallet-list-create"))
        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data

    def test_list_wallets_invalid_child_id(self, client, auth_headers):
        """Test listing with invalid child_id"""
        wallet_id = uuid.uuid4()
        response = client.get(
            f"{url_for('wallet.wallet-list-create')}?child_id={wallet_id}",
            headers=auth_headers,
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "You are not the parent".lower() in data["error"].lower()

    def test_create_wallet_user_success(
        self, client, test_user, auth_headers, db_session
    ):
        """Test user creating own wallet"""
        new_wallet = {"name": "New Wallet", "user_id": str(test_user.id)}
        response = client.post(
            url_for("wallet.wallet-list-create"), json=new_wallet, headers=auth_headers
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["name"].lower() == "new wallet".lower()
        assert float(data["balance"]) == 0.00
        db_session.delete(db_session.get(Wallet, uuid.UUID(data["id"])))
        db_session.commit()

    def test_admin_create_wallet_for_user(
        self, client, admin_headers, test_user, db_session
    ):
        """Test admin creating wallet for user"""
        new_wallet = {"name": "Admin Wallet", "user_id": str(test_user.id)}
        response = client.post(
            url_for("wallet.wallet-list-create"), json=new_wallet, headers=admin_headers
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["name"].lower() == "admin wallet".lower()
        db_session.delete(db_session.get(Wallet, uuid.UUID(data["id"])))
        db_session.commit()

    def test_create_wallet_missing_name(self, client, test_user, auth_headers):
        """Test creating wallet without name"""
        new_wallet = {"user_id": str(test_user.id)}
        response = client.post(
            url_for("wallet.wallet-list-create"), json=new_wallet, headers=auth_headers
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "name" in data["error"]

    def test_create_wallet_missing_user_id(self, client, auth_headers):
        """Test creating wallet without user_id"""
        new_wallet = {"name": "Missing User Wallet"}
        response = client.post(
            url_for("wallet.wallet-list-create"), json=new_wallet, headers=auth_headers
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "user_id" in data["error"]

    def test_create_wallet_duplicate_name(
        self, client, test_user, user_wallet, auth_headers
    ):
        """Test creating wallet with duplicate name"""
        new_wallet = {"name": "Test wallet", "user_id": str(test_user.id)}
        response = client.post(
            url_for("wallet.wallet-list-create"), json=new_wallet, headers=auth_headers
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "already exists" in data["error"]["name"].lower()

    def test_create_wallet_for_other_user(self, client, child_user, auth_headers):
        """Test user creating wallet for another (should fail)"""
        new_wallet = {"name": "Invalid Wallet", "user_id": str(child_user.id)}
        response = client.post(
            url_for("wallet.wallet-list-create"), json=new_wallet, headers=auth_headers
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "create wallets for yourself" in data["error"].get("user_id").lower()

    def test_create_wallet_for_admin_by_admin(self, client, admin_user, admin_headers):
        """Test admin creating wallet for another admin (should fail)"""
        new_wallet = {"name": "Admin Wallet", "user_id": str(admin_user.id)}
        response = client.post(
            url_for("wallet.wallet-list-create"), json=new_wallet, headers=admin_headers
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "admin users cannot have wallets" in data["error"]["user_id"].lower()

    def test_create_wallet_unauthenticated(self, client, test_user):
        """Test creating wallet without authentication"""
        new_wallet = {"name": "No Auth Wallet", "user_id": str(test_user.id)}
        response = client.post(url_for("wallet.wallet-list-create"), json=new_wallet)
        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data

    def test_create_wallet_name_too_short(self, client, test_user, auth_headers):
        """Test creating wallet with name too short"""
        new_wallet = {"name": "", "user_id": str(test_user.id)}
        response = client.post(
            url_for("wallet.wallet-list-create"), json=new_wallet, headers=auth_headers
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert (
            data["error"]["name"].lower() == "Length must be between 1 and 100.".lower()
        )

    def test_create_wallet_name_too_long(self, client, test_user, auth_headers):
        """Test creating wallet with name too long"""
        long_name = "A" * 101  # Assuming max_len = 100 from constants
        new_wallet = {"name": long_name, "user_id": str(test_user.id)}
        response = client.post(
            url_for("wallet.wallet-list-create"), json=new_wallet, headers=auth_headers
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "length" in str(data["error"]).lower()
